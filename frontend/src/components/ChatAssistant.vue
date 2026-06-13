<template>
  <div class="chat-assistant-container">
    <!-- Chat Header with Scope Selector -->
    <div class="chat-header">
      <div class="chat-header-info">
        <span class="assistant-avatar">🤖</span>
        <div>
          <h3>Assistent Literari d'IA</h3>
          <p class="status-online">En línia • Cerca intel·ligent activa</p>
        </div>
      </div>
      
      <div class="chat-scope-selector">
        <label for="chat-scope-select">Àmbit de l'assistent:</label>
        <select
          id="chat-scope-select"
          v-model="chatScope"
          class="select-custom select-chat"
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

    <!-- Message Area -->
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(msg, index) in displayMessages" 
        :key="index" 
        :class="['chat-bubble-wrapper', msg.role === 'user' ? 'user-wrapper' : 'assistant-wrapper']"
      >
        <div class="chat-avatar" v-if="msg.role !== 'user'">🤖</div>
        <div class="chat-avatar user-avatar" v-else>👤</div>
        
        <div 
          :class="['chat-bubble', msg.role === 'user' ? 'bubble-user' : 'bubble-assistant']"
          v-html="renderMarkdown(msg.text)"
        ></div>
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
import { ref, onMounted, nextTick } from 'vue'

const userInput = ref('')
const chatScope = ref(171)
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputField = ref(null)

// Historial per mostrar a la interfície
const displayMessages = ref([
  {
    role: 'model',
    text: 'Hola! Soc el teu **Assistent Literari** de les biblioteques de la DIBA. \n\nEt puc ajudar a trobar recomanacions de llibres segons les teves preferències o gèneres preferits, i comprovaré directament la seva disponibilitat al catàleg. De què et ve de gust parlar avui?'
  }
])

// Historial estructurat en format Gemini que intercanviem amb el backend
const rawHistory = ref([
  {
    role: 'model',
    parts: [
      {
        text: 'Hola! Soc el teu **Assistent Literari** de les biblioteques de la DIBA. \n\nEt puc ajudar a trobar recomanacions de llibres segons les teves preferències o gèneres preferits, i comprovaré directament la seva disponibilitat al catàleg. De què et ve de gust parlar avui?'
      }
    ]
  }
])

const suggestions = [
  "Recomana'm una novel·la negra disponible",
  "Teniu llibres d'Albert Sánchez Piñol?",
  "Busca novel·les de muntanya i natura"
]

const renderMarkdown = (text) => {
  if (!text) return ''
  // Escapar HTML per seguretat
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Negrita: **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // Cursiva: *text*
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  // Enllaços: [text](url)
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
  
  // Col·lapsar múltiples línies en blanc consecutives en un màxim de 2 salts (1 paràgraf)
  html = html.replace(/\n{3,}/g, '\n\n')

  // Processament de llistes en línies
  const lines = html.split('\n')
  let inList = false
  let resultLines = []
  
  for (let line of lines) {
    const trimmed = line.trim()
    // Identificar línies de llista que comencen amb "- " o "* "
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const content = trimmed.substring(2).trim()
      if (!inList) {
        // Eliminar possible línia en blanc precedent a la llista
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
        // Saltar línies en blanc just després del tancament de la llista
        if (trimmed === '') continue
      }
      resultLines.push(line)
    }
  }
  if (inList) {
    resultLines.push('</ul>')
  }
  
  // Convertir a HTML: dobles salts → <br>, simples → espai dins de línia
  html = resultLines.join('\n')
  html = html.replace(/\n\n/g, '<br>')
  html = html.replace(/\n/g, ' ')
  return html
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  const query = userInput.value.trim()
  if (!query || isLoading.value) return

  // Afegir missatge de l'usuari
  displayMessages.value.push({ role: 'user', text: query })
  userInput.value = ''
  isLoading.value = true
  
  scrollToBottom()

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
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
    
    // Afegir la resposta del model
    displayMessages.value.push({ role: 'model', text: data.response })
    
    // Guardar l'historial estructurat per a la següent crida
    rawHistory.value = data.history
  } catch (err) {
    console.error(err)
    displayMessages.value.push({
      role: 'model',
      text: `⚠️ **Error en connectar amb l'assistent:** ${err.message}. Si us plau, torna-ho a provar en uns instants.`
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
    // Retornar focus al input
    nextTick(() => {
      if (inputField.value) inputField.value.focus()
    })
  }
}

const useSuggestion = (text) => {
  userInput.value = text
  sendMessage()
}

onMounted(() => {
  scrollToBottom()
})
</script>
