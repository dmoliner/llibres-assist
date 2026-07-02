<template>
  <div 
    class="book-card" 
    :class="{ 'is-expanded': isCardExpanded }"
    @click="handleCardClick"
  >
    <!-- Indicator icon to click to expand -->
    <div class="expand-indicator-icon">
      {{ isCardExpanded ? '▲' : '▼' }}
    </div>

    <div class="book-main-content">
      <!-- Imatge de Portada / Placeholder -->
      <div class="book-cover-wrapper">
        <img
          v-if="book.cover_url"
          :src="book.cover_url"
          :alt="book.title"
          class="book-cover"
          loading="lazy"
        />
        <div v-else class="book-cover-placeholder">
          <span class="placeholder-icon">📖</span>
          <span class="placeholder-text">SENSE PORTADA</span>
        </div>
      </div>

      <!-- Detalls del llibre -->
      <div class="book-details">
        <div class="book-meta">
          <span v-if="category" class="category-badge">{{ category }}</span>
          <span v-else-if="isLoadingDescription" class="category-badge-loader skeleton-pulse"></span>
        </div>
        <h3 class="book-title" :title="book.title">{{ book.title }}</h3>
        <p v-if="book.author" class="book-author">{{ book.author }}</p>
        <p v-if="book.publisher" class="book-publisher">{{ book.publisher }}</p>

        <!-- Descripció Dinàmica quan està expandit -->
        <div class="book-description-container" :class="{ 'visible': isCardExpanded }">
          <div v-if="isLoadingDescription" class="desc-loader">
            <div class="skeleton-desc-line skeleton-pulse" style="width: 90%;"></div>
            <div class="skeleton-desc-line skeleton-pulse" style="width: 95%; margin-top: 0.5rem;"></div>
            <div class="skeleton-desc-line skeleton-pulse" style="width: 60%; margin-top: 0.5rem;"></div>
          </div>
          <div v-else-if="descriptionError" class="desc-error">
            ⚠️ {{ descriptionError }}
          </div>
          <div v-else-if="description" class="desc-content">
            <p class="book-description-text-full">{{ description }}</p>
          </div>
          <div v-else-if="isCardExpanded" class="desc-empty">
            No s'ha trobat cap descripció per a aquest llibre.
          </div>
        </div>
        
        <!-- Hint to expand when not expanded -->
        <div v-if="!isCardExpanded" class="expand-hint">
          Fes clic per veure la descripció de llibres.cat
        </div>
      </div>
    </div>

    <!-- Secció d'exemplars / Disponibilitat -->
    <div v-if="book.items && book.items.length" class="book-items-section">
      <div class="items-header" @click.stop="isItemsExpanded = !isItemsExpanded">
        <div class="items-summary-title">
          <span 
            class="availability-dot" 
            :class="availableItemsCount > 0 ? 'available' : 'none'"
          ></span>
          <span>Exemplars: {{ book.items.length }} ({{ availableItemsCount }} disponibles)</span>
        </div>
        <span 
          class="items-toggle-icon"
          :class="{ 'expanded': isItemsExpanded }"
        >
          ▼
        </span>
      </div>

      <!-- Llista d'exemplars expandible -->
      <ul v-show="isItemsExpanded" class="items-list">
        <li 
          v-for="(item, idx) in book.items" 
          :key="idx" 
          class="item-row"
        >
          <div class="item-loc-info">
            <span class="item-location">{{ item.location }}</span>
            <span v-if="item.signature" class="item-signature">Signatura: {{ item.signature }}</span>
            <span v-if="item.notes" class="item-signature" style="color: #94a3b8;">{{ item.notes }}</span>
          </div>
          <span 
            class="item-status-badge"
            :class="isAvailable(item.status) ? 'status-ok' : 'status-ko'"
          >
            {{ item.status }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const isCardExpanded = ref(false)
const isItemsExpanded = ref(false)
const isLoadingDescription = ref(false)
const descriptionError = ref('')

const description = ref(props.book.description)
const category = ref(props.book.category)

// Reset internal state when book changes (e.g. on new search)
watch(() => props.book, (newBook) => {
  description.value = newBook.description
  category.value = newBook.category
  isCardExpanded.value = false
  isItemsExpanded.value = false
  descriptionError.value = ''
}, { deep: true })

const handleCardClick = (event) => {
  // Ignorem el clic si és un botó interactiu o el header d'exemplars
  if (
    event.target.closest('button') || 
    event.target.closest('.items-header') || 
    event.target.closest('.item-row')
  ) {
    return
  }
  
  toggleCardExpand()
}

const toggleCardExpand = async () => {
  isCardExpanded.value = !isCardExpanded.value
  
  // Si s'expandeix i no s'ha descarregat la descripció prèviament
  if (isCardExpanded.value && !description.value && !isLoadingDescription.value) {
    isLoadingDescription.value = true
    descriptionError.value = ''
    
    try {
      const params = new URLSearchParams({
        title: props.book.title,
        author: props.book.author || '',
        publisher: props.book.publisher || ''
      })
      
      const response = await fetch(`/api/books/${props.book.id}/enrich?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`Error en obtenir descripció (${response.status})`)
      }
      
      const data = await response.json()
      description.value = data.description
      category.value = data.category
    } catch (err) {
      console.error(err)
      descriptionError.value = "No s'ha pogut obtenir la descripció."
    } finally {
      isLoadingDescription.value = false
    }
  }
}

// Comprova si un exemplar és disponible
const isAvailable = (status) => {
  if (!status) return false
  const norm = status.toLowerCase()
  return norm.includes('disponible') || norm.includes('ok')
}

// Filtra i compta quants exemplars hi ha disponibles
const availableItemsCount = computed(() => {
  if (!props.book.items) return 0
  return props.book.items.filter(item => isAvailable(item.status)).length
})
</script>
