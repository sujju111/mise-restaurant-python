<script setup lang="ts">
import { asset } from "../assets";

import { computed, ref } from "vue";
import { state, money, dispatch, toast, busy } from "../store";
import type { Dish } from "../types";
const search = ref("");
const category = ref("All dishes");
const editing = ref(false);
const error = ref("");
const price = ref(0);
const blank: Dish = {
  id: "",
  name: "",
  description: "",
  category: "House favourites",
  price: 0,
  available: true,
  image: "momo",
  dietary: "",
};
const form = ref<Dish>({ ...blank });
const categories = computed(() => [
  "All dishes",
  ...new Set(state.value!.menu.map((d) => d.category)),
]);
const dishes = computed(() =>
  state.value!.menu.filter(
    (d) =>
      (category.value === "All dishes" || d.category === category.value) &&
      `${d.name} ${d.description}`
        .toLowerCase()
        .includes(search.value.toLowerCase()),
  ),
);
function edit(d?: Dish) {
  form.value = d ? { ...d } : { ...blank };
  price.value = form.value.price / 100;
  error.value = "";
  editing.value = true;
}
async function save() {
  try {
    await dispatch("save_menu_item", {
      ...form.value,
      price: Math.round(price.value * 100),
    });
    editing.value = false;
    toast.value = "Menu updated. Your guests see the latest version.";
  } catch (e) {
    error.value = (e as Error).message;
  }
}
async function toggle(d: Dish) {
  try {
    await dispatch("save_menu_item", { ...d, available: !d.available });
    toast.value = d.available ? "Marked unavailable" : "Back on the menu";
  } catch (e) {
    toast.value = (e as Error).message;
  }
}
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="eyebrow">CURATED BY YOU</div>
      <h1>A menu with your signature.</h1>
      <p>
        Your dishes, your prices, your story. Only for
        {{ state!.restaurant.name }}.
      </p>
    </div>
    <v-btn color="primary" prepend-icon="mdi-plus" size="large" @click="edit()"
      >Add a dish</v-btn
    >
  </div>
  <div class="menu-studio-banner">
    <span class="menu-label"
      ><v-icon icon="mdi-book-open-page-variant-outline" />THE
      {{ state!.restaurant.name.toUpperCase() }} COLLECTION</span
    >
    <p>
      {{ state!.menu.length }} dishes <span>·</span>
      {{ state!.menu.filter((d) => d.available).length }} available
      <span>·</span> Published instantly to your menu
    </p>
  </div>
  <div class="menu-tools">
    <div class="category-tabs">
      <button
        v-for="c in categories"
        :key="c"
        :class="{ active: category === c }"
        @click="category = c"
      >
        {{ c }}
      </button>
    </div>
    <v-text-field
      v-model="search"
      placeholder="Find a dish…"
      aria-label="Search menu"
      prepend-inner-icon="mdi-magnify"
      hide-details
      density="compact"
    />
  </div>
  <div class="dish-grid">
    <article v-for="d in dishes" :key="d.id" class="dish-card">
      <div class="dish-image">
        <img
          :src="asset(`images/${d.image}.jpg`)"
          :alt="d.name"
          loading="lazy"
        /><span v-if="d.dietary" class="dietary-tag">{{ d.dietary }}</span
        ><button
          class="dish-edit"
          :aria-label="`Edit ${d.name}`"
          @click="edit(d)"
        >
          <v-icon icon="mdi-pencil-outline" size="18" />
        </button>
      </div>
      <div class="dish-content">
        <small>{{ d.category }}</small>
        <div class="dish-title">
          <h3>{{ d.name }}</h3>
          <strong>{{ money(d.price) }}</strong>
        </div>
        <p>{{ d.description }}</p>
        <div class="dish-footer">
          <span class="availability" :class="{ off: !d.available }"
            ><i></i>{{ d.available ? "On the menu" : "Sold out for now" }}</span
          ><v-switch
            :model-value="d.available"
            :aria-label="`Availability of ${d.name}`"
            @update:model-value="toggle(d)"
            color="primary"
            hide-details
            inset
            density="compact"
            :disabled="busy"
          />
        </div>
      </div>
    </article>
  </div>
  <div v-if="!dishes.length" class="empty-state">
    <h3>No dishes found.</h3>
    <p>Try another search or add something new.</p>
  </div>
  <v-dialog v-model="editing"
    ><v-card class="dialog-card"
      ><div class="row-between">
        <h2>{{ form.id ? "A little refinement." : "Something delicious." }}</h2>
        <v-btn
          icon="mdi-close"
          variant="text"
          aria-label="Close menu editor"
          @click="editing = false"
        />
      </div>
      <p class="muted mb-5">Make it sound like your kitchen.</p>
      <v-form @submit.prevent="save"
        ><v-text-field
          v-model="form.name"
          label="Dish name"
          required
          maxlength="100"
        /><v-textarea
          v-model="form.description"
          label="Description"
          variant="outlined"
          rows="2"
          maxlength="500"
        />
        <div class="two-fields">
          <v-text-field
            v-model.number="price"
            label="Price (NPR)"
            type="number"
            min="0.01"
            step="0.01"
            required
          /><v-combobox
            v-model="form.category"
            label="Category"
            :items="categories.filter((c) => c !== 'All dishes')"
            variant="outlined"
          />
        </div>
        <div class="two-fields">
          <v-select
            v-model="form.image"
            label="Photo collection"
            :items="['momo', 'bowl', 'curry', 'salad', 'drink', 'dessert']"
          /><v-select
            v-model="form.dietary"
            label="Dietary label"
            :items="[
              { title: 'None', value: '' },
              { title: 'Vegetarian', value: 'Vegetarian' },
              { title: 'Vegan', value: 'Vegan' },
            ]"
          />
        </div>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{
          error
        }}</v-alert
        ><v-btn color="primary" type="submit" block :loading="busy"
          >Save & publish dish</v-btn
        ></v-form
      ></v-card
    ></v-dialog
  >
</template>
