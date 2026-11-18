<template>
  <header class="page-head">
    <span class="folio" aria-hidden="true">{{ folio }}</span>
    <div class="page-head-copy">
      <p class="eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}<span class="title-dot">.</span></h1>
      <p v-if="deck" class="deck">{{ deck }}</p>
    </div>
    <div v-if="$slots.actions" class="page-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script>
export default {
  name: 'PageHead',
  props: {
    folio: { type: String, required: true },
    eyebrow: { type: String, default: '' },
    title: { type: String, required: true },
    deck: { type: String, default: '' }
  }
}
</script>
