<script setup lang="ts">
import GalleryAppBarSearch from "@/components/Gallery/AppBar/Search/Base.vue";
import FabOverlay from "@/components/Gallery/FabOverlay.vue";
import EmptySearch from "@/components/common/EmptyStates/EmptySearch.vue";
import EmptyGame from "@/components/common/EmptyStates/EmptyGame.vue";
import GameCard from "@/components/common/Game/Card/Base.vue";
import Skeleton from "@/components/Gallery/Skeleton.vue";
import GameDataTable from "@/components/common/Game/Table.vue";
import storeGalleryFilter from "@/stores/galleryFilter";
import storeGalleryView from "@/stores/galleryView";
import storeRoms, { type SimpleRom } from "@/stores/roms";
import { views } from "@/utils";
import { ROUTES } from "@/plugins/router";
import { storeToRefs } from "pinia";
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

// Props
const galleryViewStore = storeGalleryView();
const { scrolledToTop, currentView } = storeToRefs(galleryViewStore);
const galleryFilterStore = storeGalleryFilter();
const { searchText } = storeToRefs(galleryFilterStore);
const romsStore = storeRoms();
const router = useRouter();
const initialSearch = ref(false);
const {
  allRoms,
  filteredRoms,
  selectedRoms,
  currentPlatform,
  currentCollection,
  itemsPerBatch,
  gettingRoms,
} = storeToRefs(romsStore);

const itemsShown = ref(itemsPerBatch.value);
let timeout: ReturnType<typeof setTimeout>;

function onGameClick(emitData: { rom: SimpleRom; event: MouseEvent }) {
  let index = filteredRoms.value.indexOf(emitData.rom);
  if (
    emitData.event.shiftKey ||
    romsStore.selecting ||
    romsStore.selectedRoms.length > 0
  ) {
    emitData.event.preventDefault();
    emitData.event.stopPropagation();
    if (!selectedRoms.value.includes(emitData.rom)) {
      romsStore.addToSelection(emitData.rom);
    } else {
      romsStore.removeFromSelection(emitData.rom);
    }
    if (emitData.event.shiftKey) {
      const [start, end] = [romsStore.lastSelectedIndex, index].sort(
        (a, b) => a - b,
      );
      if (romsStore.selectedRoms.includes(emitData.rom)) {
        for (let i = start + 1; i < end; i++) {
          romsStore.addToSelection(filteredRoms.value[i]);
        }
      } else {
        for (let i = start; i <= end; i++) {
          romsStore.removeFromSelection(filteredRoms.value[i]);
        }
      }
      romsStore.updateLastSelected(
        romsStore.selectedRoms.includes(emitData.rom) ? index : index - 1,
      );
    } else {
      romsStore.updateLastSelected(index);
    }
  } else if (emitData.event.metaKey || emitData.event.ctrlKey) {
    const link = router.resolve({
      name: ROUTES.ROM,
      params: { rom: emitData.rom.id },
    });
    window.open(link.href, "_blank");
  } else {
    router.push({ name: ROUTES.ROM, params: { rom: emitData.rom.id } });
  }
}

function onGameTouchStart(emitData: { rom: SimpleRom; event: TouchEvent }) {
  timeout = setTimeout(() => {
    romsStore.addToSelection(emitData.rom);
  }, 500);
}

function onGameTouchEnd() {
  clearTimeout(timeout);
}

function onScroll() {
  if (currentView.value != 2) {
    window.setTimeout(async () => {
      const { scrollTop, scrollHeight, clientHeight } =
        document.documentElement;
      scrolledToTop.value = scrollTop === 0;
      const totalScrollableHeight = scrollHeight - clientHeight;
      const ninetyPercentPoint = totalScrollableHeight * 0.9;
      if (
        scrollTop >= ninetyPercentPoint &&
        itemsShown.value < filteredRoms.value.length
      ) {
        itemsShown.value = itemsShown.value + itemsPerBatch.value;
        galleryViewStore.scroll = scrollHeight;
      }
    }, 100);
    clearTimeout(timeout);
  }
}

function resetGallery() {
  romsStore.reset();
  galleryFilterStore.reset();
  galleryFilterStore.activeFilterDrawer = false;
  scrolledToTop.value = true;
  itemsShown.value = itemsPerBatch.value;
}

onMounted(async () => {
  currentPlatform.value = null;
  currentCollection.value = null;
  resetGallery();
  window.addEventListener("wheel", onScroll);
  window.addEventListener("scroll", onScroll);
  window.addEventListener("touchmove", onScroll);
});

onBeforeUnmount(() => {
  window.removeEventListener("wheel", onScroll);
  window.removeEventListener("scroll", onScroll);
  window.removeEventListener("touchmove", onScroll);
  searchText.value = "";
});
</script>

<template>
  <gallery-app-bar-search />
  <template v-if="gettingRoms">
    <skeleton />
  </template>
  <template v-else>
    <template v-if="filteredRoms.length > 0">
      <v-row v-show="currentView != 2" class="mx-1 mt-3" no-gutters>
        <!-- Gallery cards view -->
        <!-- v-show instead of v-if to avoid recalculate on view change -->
        <v-col
          v-for="rom in filteredRoms.slice(0, itemsShown)"
          :key="rom.id"
          class="pa-1 align-self-end"
          :cols="views[currentView]['size-cols']"
          :sm="views[currentView]['size-sm']"
          :md="views[currentView]['size-md']"
          :lg="views[currentView]['size-lg']"
          :xl="views[currentView]['size-xl']"
        >
          <game-card
            :key="rom.updated_at"
            :rom="rom"
            titleOnHover
            pointerOnHover
            withLink
            showFlags
            showFav
            transformScale
            showActionBar
            showPlatformIcon
            :withBorderPrimary="
              romsStore.isSimpleRom(rom) && selectedRoms?.includes(rom)
            "
            @click="onGameClick"
            @touchstart="onGameTouchStart"
            @touchend="onGameTouchEnd"
          />
        </v-col>
      </v-row>

      <!-- Gallery list view -->
      <v-row class="h-100" v-show="currentView == 2" no-gutters>
        <v-col class="h-100 pt-4 pb-2">
          <game-data-table class="h-100 mx-2" />
        </v-col>
      </v-row>
      <fab-overlay />
    </template>
    <template v-else>
      <empty-game v-if="!gettingRoms && initialSearch" />
      <empty-search v-else-if="!initialSearch" />
    </template>
  </template>
</template>
