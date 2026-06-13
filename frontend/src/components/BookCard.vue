<template>
  <div class="book-card">
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
          <span v-if="book.category" class="category-badge">{{ book.category }}</span>
        </div>
        <h3 class="book-title" :title="book.title">{{ book.title }}</h3>
        <p v-if="book.author" class="book-author">{{ book.author }}</p>
        <p v-if="book.publisher" class="book-publisher">{{ book.publisher }}</p>

        <!-- Descripció amb Toggle -->
        <div v-if="book.description" class="book-description">
          <p 
            class="book-description-text" 
            :class="{ 'expanded': isDescExpanded }"
          >
            {{ book.description }}
          </p>
          <button 
            @click="isDescExpanded = !isDescExpanded" 
            class="btn-toggle-desc"
          >
            <span>{{ isDescExpanded ? 'Veure menys' : 'Llegir descripció sencera' }}</span>
            <span>{{ isDescExpanded ? '↑' : '↓' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Secció d'exemplars / Disponibilitat -->
    <div v-if="book.items && book.items.length" class="book-items-section">
      <div class="items-header" @click="isItemsExpanded = !isItemsExpanded">
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
import { ref, computed } from 'vue'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const isDescExpanded = ref(false)
const isItemsExpanded = ref(false)

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
