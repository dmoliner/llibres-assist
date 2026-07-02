<template>
  <div class="app-container">
    <!-- Classic Search Tab Content -->
    <div v-if="activeTab === 'search'">
      <!-- Search Header -->
      <div class="app-header-unified search-header">
        <div class="header-info">
          <span class="header-logo-icon">🔍</span>
          <div>
            <h2>Tuva Clàssic</h2>
            <p class="header-subtitle">Cerca llibres a les biblioteques municipals</p>
          </div>
        </div>
        
        <!-- Three vertical dots menu -->
        <div class="header-menu-container" ref="searchMenuRef">
          <button class="btn-header-menu" @click.stop="isMenuOpen = !isMenuOpen" aria-label="Menú">
            ⋮
          </button>
          <transition name="fade-slide">
            <div v-if="isMenuOpen" class="header-dropdown-menu">
              <button 
                class="dropdown-item active" 
                disabled
              >
                <span class="dropdown-icon">🔍</span> Tuva Clàssic
              </button>
              <button 
                class="dropdown-item" 
                @click="activeTab = 'chat'; isMenuOpen = false"
              >
                <span class="dropdown-icon">🤖</span> Tuva IA
              </button>
            </div>
          </transition>
        </div>
      </div>
      <!-- Search Form -->
      <div class="search-card">
        <form @submit.prevent="performSearch">
          <div class="search-input-group">
            <div class="search-input-wrapper">
              <span class="search-icon">🔍</span>
              <input
                v-model="searchQuery"
                type="text"
                class="search-input"
                placeholder="Introdueix títol, autor o paraules clau... (ex: 'les vuit muntanyes')"
                :disabled="isLoading"
                required
              />
            </div>
            <button type="submit" class="btn-search" :disabled="isLoading">
              <span v-if="isLoading">Cercant...</span>
              <span v-else>Cerca</span>
            </button>
          </div>

          <div class="controls-row">
            <!-- Scope Selector -->
            <div class="scope-selector">
              <label for="scope-select">Àmbit de cerca:</label>
              <select
                id="scope-select"
                v-model="searchScope"
                class="select-custom"
                :disabled="isLoading"
              >
                <option :value="171">Tot el catàleg (DIBA)</option>
                <option :value="95">Barcelona Ciutat</option>
                <option :value="120">L'Hospitalet de Llobregat</option>
                <option :value="15">Badalona</option>
                <option :value="148">Terrassa</option>
                <option :value="140">Sabadell</option>
              </select>
            </div>
          </div>
        </form>
      </div>

      <!-- Error State -->
      <div v-if="errorMessage" class="error-state">
        <span class="error-icon">⚠️</span>
        <span>{{ errorMessage }}</span>
      </div>

      <!-- Loading Skeleton Grid -->
      <div v-if="isLoading" class="books-grid">
        <div v-for="n in 4" :key="n" class="skeleton-card">
          <div class="skeleton-cover skeleton-pulse"></div>
          <div class="skeleton-details">
            <div class="skeleton-title skeleton-pulse"></div>
            <div class="skeleton-author skeleton-pulse"></div>
            <div class="skeleton-publisher skeleton-pulse"></div>
            <div class="skeleton-desc skeleton-pulse"></div>
          </div>
        </div>
      </div>

      <!-- Results Grid -->
      <div v-else-if="searchResult && searchResult.books && searchResult.books.length">
        <div class="results-header">
          <div class="results-count">
            S'han trobat <span>{{ searchResult.total }}</span> resultats per a «{{ lastQuery }}»
          </div>
        </div>
        
        <div class="books-grid">
          <BookCard
            v-for="book in displayedBooks"
            :key="book.id"
            :book="book"
          />
        </div>

        <!-- Button Veure Més -->
        <div v-if="hasMoreBooks && !showAllBooks" class="more-books-actions">
          <button @click="showAllBooks = true" class="btn-more-books">
            Veure més llibres
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <div class="empty-icon">
          <span v-if="hasSearched">🔍</span>
          <span v-else>📚</span>
        </div>
        <h3 class="empty-title">
          {{ hasSearched ? 'No s\'han trobat llibres' : 'Comença la cerca' }}
        </h3>
        <p class="empty-text">
          {{ hasSearched 
            ? 'Prova de cercar amb paraules diferents o desactiva l\'enriquiment si la cerca és molt específica.' 
            : 'Introdueix paraules clau a dalt per trobar disponibilitat de llibres a les biblioteques DIBA.' 
          }}
        </p>
      </div>
    </div>

    <!-- AI Assistant Tab Content -->
    <div v-else-if="activeTab === 'chat'">
      <ChatAssistant @change-tab="activeTab = $event" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BookCard from './components/BookCard.vue'
import ChatAssistant from './components/ChatAssistant.vue'

const activeTab = ref('search')
const isMenuOpen = ref(false)
const searchMenuRef = ref(null)

const handleClickOutside = (event) => {
  if (searchMenuRef.value && !searchMenuRef.value.contains(event.target)) {
    isMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
const searchQuery = ref('')
const searchScope = ref(171)

const isLoading = ref(false)
const hasSearched = ref(false)
const errorMessage = ref('')
const searchResult = ref(null)
const lastQuery = ref('')
const showAllBooks = ref(false)

const displayedBooks = computed(() => {
  if (!searchResult.value || !searchResult.value.books) return []
  if (showAllBooks.value) return searchResult.value.books
  return searchResult.value.books.slice(0, 4)
})

const hasMoreBooks = computed(() => {
  if (!searchResult.value || !searchResult.value.books) return false
  return searchResult.value.books.length > 4
})

const performSearch = async () => {
  if (!searchQuery.value.trim()) return

  showAllBooks.value = false
  isLoading.value = true
  errorMessage.value = ''
  hasSearched.value = true
  lastQuery.value = searchQuery.value

  const queryParams = new URLSearchParams({
    q: searchQuery.value,
    desc: 'false',
    scope: searchScope.value
  })

  try {
    const response = await fetch(`/api/search?${queryParams.toString()}`)
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || `Error del servidor (${response.status})`)
    }

    const data = await response.json()
    searchResult.value = data
  } catch (err) {
    console.error(err)
    errorMessage.value = `No s'ha pogut realitzar la cerca: ${err.message}`
    searchResult.value = null
  } finally {
    isLoading.value = false
  }
}
</script>

