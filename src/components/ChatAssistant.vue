<template>
  <div class="chat-assistant-container">
    <!-- Chat Header -->
    <div class="chat-header">
      <div class="chat-header-info">
        <span class="assistant-avatar">🤖</span>
        <div>
          <h3>Tuva IA</h3>
          <p class="status-online">En línia • Cerca intel·ligent activa</p>
        </div>
      </div>
      
      <!-- Three vertical dots menu -->
      <div class="header-menu-container" ref="chatMenuRef">
        <button class="btn-header-menu" @click.stop="isMenuOpen = !isMenuOpen" aria-label="Menú">
          ⋮
        </button>
        <transition name="fade-slide">
          <div v-if="isMenuOpen" class="header-dropdown-menu">
            <button 
              class="dropdown-item" 
              @click="selectTab('search')"
            >
              <span class="dropdown-icon">🔍</span> Tuva Clàssic
            </button>
            <button 
              class="dropdown-item active" 
              disabled
            >
              <span class="dropdown-icon">🤖</span> Tuva IA
            </button>
          </div>
        </transition>
      </div>
    </div>

    <!-- Message Area -->
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(msg, index) in displayMessages" 
        :key="index" 
        :class="['chat-bubble-wrapper', msg.role === 'user' ? 'user-wrapper' : 'assistant-wrapper']"
      >
        <div class="chat-avatar" v-if="msg.role !== 'user'">🤖</div>
        <div class="chat-avatar user-avatar" v-else>👤</div>
        
        <!-- Missatge d'usuari: sempre text pla -->
        <div v-if="msg.role === 'user'" class="chat-bubble bubble-user" v-html="renderMarkdown(msg.text)"></div>
        
        <!-- Missatge de l'assistent: amb o sense targetes de llibres -->
        <div v-else class="chat-bubble bubble-assistant">
          <!-- Text introductori (preamble) -->
          <div v-if="msg.books && msg.books.length > 0 && msg.preamble" class="bubble-text" v-html="renderMarkdown(msg.preamble)"></div>

          <!-- Targetes de llibres -->
          <div v-if="msg.books && msg.books.length > 0" class="chat-book-cards">
            <div
              v-for="(book, bi) in (msg.expanded ? msg.books : msg.books.slice(0, 3))"
              :key="bi"
              class="chat-book-card"
            >
              <div class="chat-book-card-header">
                <div class="chat-book-card-title-block">
                  <span class="chat-book-card-title">{{ book.title }}</span>
                  <span class="chat-book-card-author" v-if="book.author">{{ book.author }}</span>
                </div>
                <span :class="['chat-book-avail-badge', book.isAvailable ? 'avail-yes' : 'avail-no']">
                  {{ book.isAvailable ? '🟢' : '🔴' }} {{ book.availabilityText }}
                </span>
              </div>
              <div v-if="book.locations" class="chat-book-card-locations">
                📍 
                <span class="locations-text">
                  {{ getDisplayedLocations(book) }}
                </span>
                <button 
                  v-if="hasMoreLocations(book)" 
                  class="btn-toggle-locations"
                  @click.stop="book.expandedLocations = !book.expandedLocations"
                >
                  {{ book.expandedLocations ? 'Amagar' : `+${getMoreLocationsCount(book)} biblioteques` }}
                </button>
              </div>
            </div>

            <!-- Botó Veure més resultats -->
            <button
              v-if="!msg.expanded && msg.books.length > 3"
              @click="msg.expanded = true"
              class="btn-show-more-books"
            >
              Veure {{ msg.books.length - 3 }} resultat{{ msg.books.length - 3 !== 1 ? 's' : '' }} més →
            </button>
          </div>

          <!-- Text de tancament (postamble) -->
          <div v-if="msg.books && msg.books.length > 0 && msg.postamble" class="bubble-text bubble-postamble" v-html="renderMarkdown(msg.postamble)"></div>

          <!-- Missatge sense targetes (fallback text pla) -->
          <div v-if="!msg.books || msg.books.length === 0" v-html="renderMarkdown(msg.text)"></div>
        </div>
      </div>

      <!-- Loading State / Thinking -->
      <div v-if="isLoading" class="chat-bubble-wrapper assistant-wrapper">
        <div class="chat-avatar">🤖</div>
        <div class="chat-bubble bubble-assistant thinking-bubble">
          <span class="thinking-dots">
            <span>.</span><span>.</span><span>.</span>
          </span>
          <span class="thinking-text">Consultant el catàleg i processant recomanació...</span>
        </div>
      </div>
    </div>

    <!-- Chat Input Area -->
    <div class="chat-input-area">
      <form @submit.prevent="sendMessage" class="chat-form">
        <input
          v-model="userInput"
          type="text"
          class="chat-input-field"
          placeholder="Demana recomanacions o pregunta per un llibre... (ex: 'Busca novel·les de Mercè Rodoreda')"
          :disabled="isLoading"
          required
          ref="inputField"
        />
        <button type="submit" class="btn-send-message" :disabled="isLoading || !userInput.trim()">
          <span class="send-icon">➔</span>
        </button>
      </form>
      <div class="chat-suggestions">
        <button 
          v-for="suggestion in suggestions" 
          :key="suggestion"
          @click="useSuggestion(suggestion)"
          :disabled="isLoading"
          class="btn-suggestion"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const emit = defineEmits(['change-tab'])

const userInput = ref('')
const chatScope = ref(171)
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputField = ref(null)

const isMenuOpen = ref(false)
const chatMenuRef = ref(null)

const selectTab = (tab) => {
  isMenuOpen.value = false
  emit('change-tab', tab)
}

const handleClickOutside = (event) => {
  if (chatMenuRef.value && !chatMenuRef.value.contains(event.target)) {
    isMenuOpen.value = false
  }
}

// ── Parser de missatges ─────────────────────────────────────────────────────

/**
 * Dona format llegible a la part de text d'un element de llista.
 * Elimina el markdown de negreta/cursiva per mostrar text net.
 */
function stripMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .trim()
}

/**
 * Analitza el text brut de la IA i extreu:
 * - preamble: text introductor
 * - books: array d'objectes de llibre estructurats
 * - postamble: text de cloenda
 */
function parseMessageContent(rawText) {
  const lines = rawText.split('\n')
  const preambleLines = []
  const postambleLines = []
  const books = []
  let currentBook = null
  let inBookList = false
  let listDone = false

  const isListItem = (line) => line.trim().startsWith('- ') || line.trim().startsWith('* ')
  const getContent = (line) => line.trim().substring(2).trim()

  for (const line of lines) {
    const trimmed = line.trim()

    if (!inBookList && !listDone) {
      if (isListItem(line)) {
        const content = getContent(line)
        if (content.includes('📖')) {
          // Inici de la secció de llibres
          inBookList = true
          currentBook = parseBookTitle(content)
        } else {
          preambleLines.push(line)
        }
      } else {
        preambleLines.push(line)
      }
    } else if (inBookList) {
      if (isListItem(line)) {
        const content = getContent(line)
        if (content.includes('📖')) {
          if (currentBook) books.push(currentBook)
          currentBook = parseBookTitle(content)
        } else if (content.includes('🟢') || content.includes('🔴')) {
          if (currentBook) {
            const isAvailable = content.includes('🟢')
            currentBook.isAvailable = isAvailable
            currentBook.availabilityText = stripMarkdown(
              content.replace('🟢', '').replace('🔴', '').trim()
            )
          }
        } else if (content.includes('📍')) {
          if (currentBook) {
            currentBook.locations = content
              .replace(/^📍\s*\*?Ubicacions:?\*?\s*/i, '')
              .replace(/\*/g, '')
              .trim()
          }
        }
      } else if (trimmed === '') {
        // Línia en blanc dins la llista → ignorar
      } else {
        // Fi de la secció de llibres
        if (currentBook) { books.push(currentBook); currentBook = null }
        inBookList = false
        listDone = true
        if (trimmed !== '') postambleLines.push(line)
      }
    } else {
      postambleLines.push(line)
    }
  }

  if (currentBook) books.push(currentBook)

  return {
    preamble: preambleLines.join('\n').trim(),
    books,
    postamble: postambleLines.join('\n').trim()
  }
}

function parseBookTitle(content) {
  // Format: **📖 TITLE** - *Author* o **📖 TITLE** - *Author*
  const match = content.match(/\*\*📖\s*(.*?)\*\*\s*(?:-\s*\*?(.*?)\*?)?$/)
  if (match) {
    return {
      title: match[1]?.trim() || '',
      author: match[2]?.replace(/\*/g, '').trim() || '',
      availabilityText: '',
      isAvailable: false,
      locations: '',
      expandedLocations: false
    }
  }
  return {
    title: stripMarkdown(content.replace('📖', '').trim()),
    author: '',
    availabilityText: '',
    isAvailable: false,
    locations: '',
    expandedLocations: false
  }
}

// ── Historial de missatges ──────────────────────────────────────────────────

const WELCOME_TEXT = 'Hola! Soc la **Tuva IA**, l\'assistent de les biblioteques de la DIBA. \n\nEt puc ajudar a trobar recomanacions de llibres segons les teves preferències o gèneres preferits, i comprovaré directament la seva disponibilitat al catàleg. De què et ve de gust parlar avui?'

const displayMessages = ref([
  { role: 'model', text: WELCOME_TEXT, books: [], preamble: WELCOME_TEXT, postamble: '', expanded: false }
])

const rawHistory = ref([
  { role: 'model', parts: [{ text: WELCOME_TEXT }] }
])

const suggestions = [
  "Recomana'm una novel·la negra disponible",
  "Teniu llibres d'Albert Sánchez Piñol?",
  "Busca novel·les de muntanya i natura"
]

// ── Render de Markdown (per text pla sense targetes) ──────────────────────

const renderMarkdown = (text) => {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

  // Col·lapsar múltiples línies en blanc
  html = html.replace(/\n{3,}/g, '\n\n')

  // Processament de llistes
  const lines = html.split('\n')
  let inList = false
  let resultLines = []

  for (let line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const content = trimmed.substring(2).trim()
      if (!inList) {
        if (resultLines.length > 0 && resultLines[resultLines.length - 1].trim() === '') {
          resultLines.pop()
        }
        resultLines.push('<ul class="chat-list">')
        inList = true
      }
      resultLines.push(`<li>${content}</li>`)
    } else {
      if (inList) {
        resultLines.push('</ul>')
        inList = false
        if (trimmed === '') continue
      }
      resultLines.push(line)
    }
  }
  if (inList) resultLines.push('</ul>')

  html = resultLines.join('\n')
  html = html.replace(/\n\n/g, '<br>')
  html = html.replace(/\n/g, ' ')
  return html
}

// ── Navegació i enviament ──────────────────────────────────────────────────

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
  // Desplaça la finestra de la pàgina a sota per assegurar que el quadre de text és visible
  window.scrollTo({
    top: document.documentElement.scrollHeight || document.body.scrollHeight,
    behavior: 'smooth'
  })
}

const sendMessage = async () => {
  const query = userInput.value.trim()
  if (!query || isLoading.value) return

  displayMessages.value.push({ role: 'user', text: query, books: [], preamble: '', postamble: '', expanded: false })
  userInput.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    const apiBase = import.meta.env.VITE_API_URL || ''
    const response = await fetch(`${apiBase}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: query,
        history: rawHistory.value,
        scope: chatScope.value
      })
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || `Error del servidor (${response.status})`)
    }

    const data = await response.json()
    const parsed = parseMessageContent(data.response)

    displayMessages.value.push({
      role: 'model',
      text: data.response,
      preamble: parsed.preamble,
      books: parsed.books,
      postamble: parsed.postamble,
      expanded: false
    })

    rawHistory.value = data.history
  } catch (err) {
    console.error(err)
    const errText = `⚠️ **Error en connectar amb l'assistent:** ${err.message}. Si us plau, torna-ho a provar en uns instants.`
    displayMessages.value.push({ role: 'model', text: errText, books: [], preamble: errText, postamble: '', expanded: false })
  } finally {
    isLoading.value = false
    scrollToBottom()
    nextTick(() => { if (inputField.value) inputField.value.focus() })
  }
}

const getLocationsArray = (locationsStr) => {
  if (!locationsStr) return []
  return locationsStr.split(',').map(l => l.trim()).filter(Boolean)
}

const hasMoreLocations = (book) => {
  return getLocationsArray(book.locations).length > 2
}

const getMoreLocationsCount = (book) => {
  const arr = getLocationsArray(book.locations)
  return Math.max(0, arr.length - 2)
}

const getDisplayedLocations = (book) => {
  const arr = getLocationsArray(book.locations)
  if (book.expandedLocations || arr.length <= 2) {
    return book.locations
  }
  return arr.slice(0, 2).join(', ') + '...'
}

const useSuggestion = (text) => {
  userInput.value = text
  sendMessage()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  scrollToBottom()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
