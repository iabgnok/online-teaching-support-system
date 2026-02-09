<template>
  <div class="whiteboard-container">
    <!-- 左侧工具栏 -->
    <div v-if="!readonly" class="toolbar-left">
      <!-- 绘图工具组 -->
      <div class="tool-group">
        <div class="tool-group-label">绘图</div>
        <button 
          class="tool-btn" 
          :class="{ active: currentTool === 'pen' }"
          @click="setTool('pen')"
          title="画笔 (P)"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 19l7-7 3 3-7 7-3-3z"></path>
            <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path>
            <path d="M2 2l7.586 7.586"></path>
            <circle cx="11" cy="11" r="2"></circle>
          </svg>
          <span class="tool-label">画笔</span>
        </button>
        
        <button 
          class="tool-btn" 
          :class="{ active: currentTool === 'highlighter' }"
          @click="setTool('highlighter')"
          title="荧光笔 (H)"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 11l-6 6v3h9l3-3"></path>
            <path d="M22 12l-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"></path>
          </svg>
          <span class="tool-label">荧光笔</span>
        </button>
        
        <button 
          class="tool-btn" 
          :class="{ active: currentTool === 'eraser' }"
          @click="setTool('eraser')"
          title="橡皮 (E)"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 20H7L3 16c-.8-.8-.8-2 0-2.8L13.2 3a2 2 0 0 1 2.8 0L21 8a2 2 0 0 1 0 2.8L12 20"></path>
            <path d="M6 11l5 5"></path>
          </svg>
          <span class="tool-label">橡皮</span>
        </button>
      </div>
      
      <!-- 形状工具组 -->
      <div class="tool-group">
        <div class="tool-group-label">形状</div>
        <button 
          class="tool-btn" 
          :class="{ active: currentTool === 'line' }"
          @click="setTool('line')"
          title="直线 (L)"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="5" y1="19" x2="19" y2="5"></line>
          </svg>
          <span class="tool-label">直线</span>
        </button>
        
        <button 
          class="tool-btn" 
          :class="{ active: currentTool === 'arrow' }"
          @click="setTool('arrow')"
          title="箭头 (A)"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="5" y1="19" x2="19" y2="5"></line>
            <polyline points="10 5 19 5 19 14"></polyline>
          </svg>
          <span class="tool-label">箭头</span>
        </button>
        
        <button 
          class="tool-btn" 
          :class="{ active: currentTool === 'rect' }"
          @click="setTool('rect')"
          title="矩形 (R)"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          </svg>
          <span class="tool-label">矩形</span>
        </button>
        
        <button 
          class="tool-btn" 
          :class="{ active: currentTool === 'circle' }"
          @click="setTool('circle')"
          title="椭圆 (O)"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
          </svg>
          <span class="tool-label">椭圆</span>
        </button>
      </div>
      
      <!-- 文本工具 -->
      <div class="tool-group">
        <div class="tool-group-label">文本</div>
        <button 
          class="tool-btn" 
          :class="{ active: currentTool === 'text' }"
          @click="setTool('text')"
          title="文本 (T)"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="4 7 4 4 20 4 20 7"></polyline>
            <line x1="12" y1="4" x2="12" y2="20"></line>
            <line x1="8" y1="20" x2="16" y2="20"></line>
          </svg>
          <span class="tool-label">文本</span>
        </button>
      </div>
      
      <!-- 颜色和大小 -->
      <div class="tool-group">
        <div class="tool-group-label">样式</div>
        
        <!-- 颜色选择 -->
        <div class="color-picker-wrapper">
          <div 
            class="color-preview" 
            :style="{ backgroundColor: currentColor }"
            @click="showColorPicker = !showColorPicker"
          ></div>
          <div v-if="showColorPicker" class="color-palette">
            <div 
              v-for="color in colorPalette" 
              :key="color"
              class="color-swatch"
              :style="{ backgroundColor: color }"
              :class="{ active: currentColor === color }"
              @click="selectColor(color)"
            ></div>
            <input 
              type="color" 
              v-model="customColor"
              @change="selectColor(customColor)"
              class="custom-color-input"
            />
          </div>
        </div>
        
        <!-- 笔刷大小 -->
        <div class="size-control">
          <div class="size-preview" :style="{ width: brushSize + 'px', height: brushSize + 'px' }"></div>
          <input 
            type="range" 
            v-model.number="brushSize" 
            min="1" 
            max="30" 
            class="size-slider"
            orient="vertical"
          />
          <span class="size-value">{{ brushSize }}px</span>
        </div>
      </div>
      
      <!-- 操作组 -->
      <div class="tool-group">
        <div class="tool-group-label">操作</div>
        
        <button class="tool-btn" @click="undo" title="撤销 (Ctrl+Z)" :disabled="!canUndo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="1 4 1 10 7 10"></polyline>
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
          </svg>
          <span class="tool-label">撤销</span>
        </button>
        
        <button class="tool-btn" @click="redo" title="重做 (Ctrl+Y)" :disabled="!canRedo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
          </svg>
          <span class="tool-label">重做</span>
        </button>
        
        <button class="tool-btn" @click="clearCanvas" title="清空画板">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          <span class="tool-label">清空</span>
        </button>
      </div>
      
      <!-- 媒体组 -->
      <div class="tool-group">
        <div class="tool-group-label">媒体</div>
        
        <button class="tool-btn" @click="triggerImageUpload" title="插入图片">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          <span class="tool-label">图片</span>
        </button>
        
        <button class="tool-btn" @click="downloadCanvas" title="下载画板">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span class="tool-label">下载</span>
        </button>
        
        <input 
          ref="imageInput" 
          type="file" 
          accept="image/*" 
          @change="handleImageUpload" 
          style="display: none"
        />
      </div>
    </div>
    
    <!-- 画布区域 -->
    <div class="canvas-area" :class="{ 'readonly': readonly }">
      <!-- 背景图片层 -->
      <img 
        v-if="backgroundImage" 
        :src="backgroundImage" 
        class="canvas-background"
        @load="onBackgroundLoad"
      />
      
      <!-- 主画布 -->
      <canvas
        ref="mainCanvas"
        class="main-canvas"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
        @touchstart.prevent="handleTouchStart"
        @touchmove.prevent="handleTouchMove"
        @touchend="handleTouchEnd"
      ></canvas>
      
      <!-- 临时画布（用于形状预览） -->
      <canvas
        ref="tempCanvas"
        class="temp-canvas"
      ></canvas>
      
      <!-- 文本输入框 -->
      <textarea
        v-if="isTextEditing"
        ref="textInput"
        v-model="textContent"
        class="text-input"
        :style="textInputStyle"
        @blur="finishTextInput"
        @keydown.enter.exact="finishTextInput"
        @keydown.esc="cancelTextInput"
      ></textarea>
      
      <!-- 只读模式提示 -->
      <div v-if="readonly" class="readonly-overlay">
        <span class="readonly-hint">👀 观看模式</span>
      </div>
    </div>
    
    <!-- 缩放控制 -->
    <div class="zoom-controls">
      <button class="zoom-btn" @click="zoomOut" title="缩小">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
      </button>
      <span class="zoom-value">{{ Math.round(zoomLevel * 100) }}%</span>
      <button class="zoom-btn" @click="zoomIn" title="放大">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
      </button>
      <button class="zoom-btn" @click="resetZoom" title="重置">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
          <path d="M3 3v5h5"></path>
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

export default {
  name: 'WhiteBoard',
  props: {
    lessonId: {
      type: String,
      required: true
    },
    readonly: {
      type: Boolean,
      default: false
    },
    socket: {
      type: Object,
      default: null
    }
  },
  emits: ['board-updated'],
  setup(props, { emit }) {
    // ========== Refs ==========
    const mainCanvas = ref(null)
    const tempCanvas = ref(null)
    const imageInput = ref(null)
    const textInput = ref(null)
    
    // ========== State ==========
    const currentTool = ref('pen')
    const currentColor = ref('#000000')
    const customColor = ref('#000000')
    const brushSize = ref(3)
    const showColorPicker = ref(false)
    const backgroundImage = ref(null)
    const zoomLevel = ref(1)
    
    // 绘制状态
    const isDrawing = ref(false)
    const startPoint = reactive({ x: 0, y: 0 })
    const lastPoint = reactive({ x: 0, y: 0 })
    
    // 文本输入
    const isTextEditing = ref(false)
    const textContent = ref('')
    const textPosition = reactive({ x: 0, y: 0 })
    
    // 历史记录（用于撤销/重做）
    const history = ref([])
    const historyIndex = ref(-1)
    const maxHistory = 50
    
    // 颜色面板
    const colorPalette = [
      '#000000', '#ffffff', '#ff0000', '#00ff00', '#0000ff',
      '#ffff00', '#ff00ff', '#00ffff', '#ff6600', '#6600ff',
      '#006600', '#660000', '#003366', '#ff99cc', '#99ccff'
    ]
    
    // ========== Computed ==========
    const canUndo = computed(() => historyIndex.value > 0)
    const canRedo = computed(() => historyIndex.value < history.value.length - 1)
    
    const textInputStyle = computed(() => ({
      left: textPosition.x + 'px',
      top: textPosition.y + 'px',
      color: currentColor.value,
      fontSize: brushSize.value * 4 + 'px'
    }))
    
    // ========== Canvas Context ==========
    let ctx = null
    let tempCtx = null
    
    // ========== Methods ==========
    const initCanvas = () => {
      if (!mainCanvas.value || !tempCanvas.value) return
      
      ctx = mainCanvas.value.getContext('2d', { willReadFrequently: true })
      tempCtx = tempCanvas.value.getContext('2d', { willReadFrequently: true })
      
      resizeCanvas()
      window.addEventListener('resize', resizeCanvas)
      
      // 保存初始状态
      saveHistory()
    }
    
    const resizeCanvas = () => {
      if (!mainCanvas.value) return
      
      const container = mainCanvas.value.parentElement
      const rect = container.getBoundingClientRect()
      
      // 保存当前内容
      const imageData = ctx ? ctx.getImageData(0, 0, mainCanvas.value.width, mainCanvas.value.height) : null
      
      mainCanvas.value.width = rect.width
      mainCanvas.value.height = rect.height
      tempCanvas.value.width = rect.width
      tempCanvas.value.height = rect.height
      
      // 恢复内容
      if (imageData && ctx) {
        ctx.putImageData(imageData, 0, 0)
      }
      
      // 重新设置画布样式
      if (ctx) {
        ctx.lineCap = 'round'
        ctx.lineJoin = 'round'
      }
    }
    
    const setTool = (tool) => {
      currentTool.value = tool
      showColorPicker.value = false
      
      if (tool === 'text') {
        mainCanvas.value.style.cursor = 'text'
      } else if (tool === 'eraser') {
        mainCanvas.value.style.cursor = 'crosshair'
      } else {
        mainCanvas.value.style.cursor = 'crosshair'
      }
    }
    
    const selectColor = (color) => {
      currentColor.value = color
      showColorPicker.value = false
    }
    
    const getEventPoint = (e) => {
      const rect = mainCanvas.value.getBoundingClientRect()
      const clientX = e.touches ? e.touches[0].clientX : e.clientX
      const clientY = e.touches ? e.touches[0].clientY : e.clientY
      return {
        x: (clientX - rect.left) / zoomLevel.value,
        y: (clientY - rect.top) / zoomLevel.value
      }
    }
    
    const handleMouseDown = (e) => {
      if (props.readonly) return
      
      const point = getEventPoint(e)
      startPoint.x = point.x
      startPoint.y = point.y
      lastPoint.x = point.x
      lastPoint.y = point.y
      
      if (currentTool.value === 'text') {
        textPosition.x = point.x
        textPosition.y = point.y
        isTextEditing.value = true
        nextTick(() => textInput.value?.focus())
        return
      }
      
      isDrawing.value = true
      
      // 自由绘制工具立即开始绘制
      if (['pen', 'highlighter', 'eraser'].includes(currentTool.value)) {
        beginPath(point)
      }
    }
    
    const handleMouseMove = (e) => {
      if (!isDrawing.value || props.readonly) return
      
      const point = getEventPoint(e)
      
      if (['pen', 'highlighter', 'eraser'].includes(currentTool.value)) {
        // 自由绘制
        drawLine(lastPoint, point)
        lastPoint.x = point.x
        lastPoint.y = point.y
        
        // 发送到服务器
        emitDrawing({
          type: 'draw',
          tool: currentTool.value,
          from: { ...lastPoint },
          to: point,
          color: currentColor.value,
          size: brushSize.value
        })
      } else {
        // 形状预览
        drawShapePreview(point)
      }
    }
    
    const handleMouseUp = (e) => {
      if (!isDrawing.value || props.readonly) return
      
      const point = getEventPoint(e)
      
      // 形状工具完成绘制
      if (['line', 'arrow', 'rect', 'circle'].includes(currentTool.value)) {
        drawShape(startPoint, point)
        clearTempCanvas()
        
        // 发送形状到服务器
        emitDrawing({
          type: 'shape',
          tool: currentTool.value,
          from: { ...startPoint },
          to: point,
          color: currentColor.value,
          size: brushSize.value
        })
      }
      
      isDrawing.value = false
      saveHistory()
    }
    
    const handleTouchStart = (e) => handleMouseDown(e)
    const handleTouchMove = (e) => handleMouseMove(e)
    const handleTouchEnd = (e) => handleMouseUp(e)
    
    const beginPath = (point) => {
      ctx.beginPath()
      ctx.moveTo(point.x, point.y)
      applyToolStyle()
    }
    
    const applyToolStyle = () => {
      if (currentTool.value === 'eraser') {
        ctx.globalCompositeOperation = 'destination-out'
        ctx.strokeStyle = 'rgba(0,0,0,1)'
        ctx.lineWidth = brushSize.value * 3
      } else if (currentTool.value === 'highlighter') {
        ctx.globalCompositeOperation = 'multiply'
        ctx.strokeStyle = currentColor.value
        ctx.lineWidth = brushSize.value * 3
        ctx.globalAlpha = 0.3
      } else {
        ctx.globalCompositeOperation = 'source-over'
        ctx.strokeStyle = currentColor.value
        ctx.lineWidth = brushSize.value
        ctx.globalAlpha = 1
      }
    }
    
    const drawLine = (from, to) => {
      applyToolStyle()
      ctx.beginPath()
      ctx.moveTo(from.x, from.y)
      ctx.lineTo(to.x, to.y)
      ctx.stroke()
      ctx.globalAlpha = 1
    }
    
    const drawShapePreview = (point) => {
      clearTempCanvas()
      tempCtx.strokeStyle = currentColor.value
      tempCtx.lineWidth = brushSize.value
      tempCtx.lineCap = 'round'
      tempCtx.lineJoin = 'round'
      
      tempCtx.beginPath()
      
      switch (currentTool.value) {
        case 'line':
          tempCtx.moveTo(startPoint.x, startPoint.y)
          tempCtx.lineTo(point.x, point.y)
          break
        case 'arrow':
          drawArrow(tempCtx, startPoint, point)
          break
        case 'rect':
          tempCtx.rect(startPoint.x, startPoint.y, point.x - startPoint.x, point.y - startPoint.y)
          break
        case 'circle':
          const rx = Math.abs(point.x - startPoint.x) / 2
          const ry = Math.abs(point.y - startPoint.y) / 2
          const cx = startPoint.x + (point.x - startPoint.x) / 2
          const cy = startPoint.y + (point.y - startPoint.y) / 2
          tempCtx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2)
          break
      }
      
      tempCtx.stroke()
    }
    
    const drawShape = (from, to) => {
      ctx.strokeStyle = currentColor.value
      ctx.lineWidth = brushSize.value
      ctx.globalCompositeOperation = 'source-over'
      ctx.globalAlpha = 1
      
      ctx.beginPath()
      
      switch (currentTool.value) {
        case 'line':
          ctx.moveTo(from.x, from.y)
          ctx.lineTo(to.x, to.y)
          break
        case 'arrow':
          drawArrow(ctx, from, to)
          break
        case 'rect':
          ctx.rect(from.x, from.y, to.x - from.x, to.y - from.y)
          break
        case 'circle':
          const rx = Math.abs(to.x - from.x) / 2
          const ry = Math.abs(to.y - from.y) / 2
          const cx = from.x + (to.x - from.x) / 2
          const cy = from.y + (to.y - from.y) / 2
          ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2)
          break
      }
      
      ctx.stroke()
    }
    
    const drawArrow = (context, from, to) => {
      const headLength = 15
      const angle = Math.atan2(to.y - from.y, to.x - from.x)
      
      context.moveTo(from.x, from.y)
      context.lineTo(to.x, to.y)
      context.moveTo(to.x, to.y)
      context.lineTo(
        to.x - headLength * Math.cos(angle - Math.PI / 6),
        to.y - headLength * Math.sin(angle - Math.PI / 6)
      )
      context.moveTo(to.x, to.y)
      context.lineTo(
        to.x - headLength * Math.cos(angle + Math.PI / 6),
        to.y - headLength * Math.sin(angle + Math.PI / 6)
      )
    }
    
    const clearTempCanvas = () => {
      tempCtx.clearRect(0, 0, tempCanvas.value.width, tempCanvas.value.height)
    }
    
    const finishTextInput = () => {
      if (!textContent.value.trim()) {
        cancelTextInput()
        return
      }
      
      ctx.font = `${brushSize.value * 4}px Arial`
      ctx.fillStyle = currentColor.value
      ctx.globalCompositeOperation = 'source-over'
      ctx.globalAlpha = 1
      ctx.fillText(textContent.value, textPosition.x, textPosition.y + brushSize.value * 4)
      
      // 发送文本到服务器
      emitDrawing({
        type: 'text',
        content: textContent.value,
        position: { x: textPosition.x, y: textPosition.y },
        color: currentColor.value,
        size: brushSize.value * 4
      })
      
      textContent.value = ''
      isTextEditing.value = false
      saveHistory()
    }
    
    const cancelTextInput = () => {
      textContent.value = ''
      isTextEditing.value = false
    }
    
    // 历史记录
    const saveHistory = () => {
      if (!ctx || !mainCanvas.value) return
      
      // 移除当前位置之后的历史
      history.value = history.value.slice(0, historyIndex.value + 1)
      
      // 保存当前状态
      const imageData = mainCanvas.value.toDataURL()
      history.value.push(imageData)
      
      // 限制历史记录数量
      if (history.value.length > maxHistory) {
        history.value.shift()
      }
      
      historyIndex.value = history.value.length - 1
    }
    
    const undo = () => {
      if (!canUndo.value) return
      
      historyIndex.value--
      restoreFromHistory()
    }
    
    const redo = () => {
      if (!canRedo.value) return
      
      historyIndex.value++
      restoreFromHistory()
    }
    
    const restoreFromHistory = () => {
      const imageData = history.value[historyIndex.value]
      const img = new Image()
      img.onload = () => {
        ctx.clearRect(0, 0, mainCanvas.value.width, mainCanvas.value.height)
        ctx.drawImage(img, 0, 0)
      }
      img.src = imageData
    }
    
    const clearCanvas = () => {
      if (!ctx || !mainCanvas.value) return
      
      ctx.clearRect(0, 0, mainCanvas.value.width, mainCanvas.value.height)
      saveHistory()
      
      emitDrawing({ type: 'clear' })
    }
    
    // 图片
    const triggerImageUpload = () => {
      imageInput.value?.click()
    }
    
    const handleImageUpload = async (e) => {
      const file = e.target.files[0]
      if (!file) return
      
      const reader = new FileReader()
      reader.onload = (event) => {
        const img = new Image()
        img.onload = () => {
          // 缩放图片以适应画布
          const scale = Math.min(
            mainCanvas.value.width / img.width,
            mainCanvas.value.height / img.height,
            1
          )
          const width = img.width * scale
          const height = img.height * scale
          const x = (mainCanvas.value.width - width) / 2
          const y = (mainCanvas.value.height - height) / 2
          
          ctx.drawImage(img, x, y, width, height)
          saveHistory()
          
          emitDrawing({
            type: 'image',
            data: event.target.result,
            x, y, width, height
          })
        }
        img.src = event.target.result
      }
      reader.readAsDataURL(file)
      
      e.target.value = ''
    }
    
    const onBackgroundLoad = () => {
      resizeCanvas()
    }
    
    // 下载
    const downloadCanvas = () => {
      const link = document.createElement('a')
      link.download = `whiteboard_${props.lessonId}_${Date.now()}.png`
      link.href = mainCanvas.value.toDataURL()
      link.click()
    }
    
    // 缩放
    const zoomIn = () => {
      zoomLevel.value = Math.min(zoomLevel.value + 0.1, 3)
    }
    
    const zoomOut = () => {
      zoomLevel.value = Math.max(zoomLevel.value - 0.1, 0.5)
    }
    
    const resetZoom = () => {
      zoomLevel.value = 1
    }
    
    // Socket通信
    const emitDrawing = (data) => {
      if (!props.socket) return
      
      props.socket.emit('classroom:board_draw', {
        lesson_id: props.lessonId,
        ...data
      })
      
      emit('board-updated', data)
    }
    
    const receiveDrawing = (data) => {
      if (!ctx) return
      
      switch (data.type) {
        case 'draw':
          ctx.strokeStyle = data.color
          ctx.lineWidth = data.size
          if (data.tool === 'eraser') {
            ctx.globalCompositeOperation = 'destination-out'
            ctx.lineWidth = data.size * 3
          } else if (data.tool === 'highlighter') {
            ctx.globalCompositeOperation = 'multiply'
            ctx.globalAlpha = 0.3
          } else {
            ctx.globalCompositeOperation = 'source-over'
            ctx.globalAlpha = 1
          }
          ctx.beginPath()
          ctx.moveTo(data.from.x, data.from.y)
          ctx.lineTo(data.to.x, data.to.y)
          ctx.stroke()
          ctx.globalAlpha = 1
          break
          
        case 'shape':
          drawShape(data.from, data.to)
          break
          
        case 'text':
          ctx.font = `${data.size}px Arial`
          ctx.fillStyle = data.color
          ctx.fillText(data.content, data.position.x, data.position.y + data.size)
          break
          
        case 'clear':
          ctx.clearRect(0, 0, mainCanvas.value.width, mainCanvas.value.height)
          break
          
        case 'image':
          const img = new Image()
          img.onload = () => {
            ctx.drawImage(img, data.x, data.y, data.width, data.height)
          }
          img.src = data.data
          break
      }
    }
    
    // 设置背景图
    const setBackgroundImage = (imageUrl) => {
      backgroundImage.value = imageUrl
    }
    
    // 键盘快捷键
    const handleKeyDown = (e) => {
      if (props.readonly) return
      
      // Ctrl+Z: 撤销
      if (e.ctrlKey && e.key === 'z') {
        e.preventDefault()
        undo()
      }
      // Ctrl+Y: 重做
      if (e.ctrlKey && e.key === 'y') {
        e.preventDefault()
        redo()
      }
      // 工具快捷键
      if (!e.ctrlKey && !e.altKey) {
        switch (e.key.toLowerCase()) {
          case 'p': setTool('pen'); break
          case 'h': setTool('highlighter'); break
          case 'e': setTool('eraser'); break
          case 'l': setTool('line'); break
          case 'a': setTool('arrow'); break
          case 'r': setTool('rect'); break
          case 'o': setTool('circle'); break
          case 't': setTool('text'); break
        }
      }
    }
    
    // ========== Lifecycle ==========
    onMounted(() => {
      initCanvas()
      window.addEventListener('keydown', handleKeyDown)
      
      // 监听Socket事件
      if (props.socket) {
        props.socket.on('classroom:board_draw', receiveDrawing)
        props.socket.on('classroom:board_image', (data) => {
          setBackgroundImage(data.imageUrl)
        })
      }
    })
    
    onBeforeUnmount(() => {
      window.removeEventListener('resize', resizeCanvas)
      window.removeEventListener('keydown', handleKeyDown)
      
      if (props.socket) {
        props.socket.off('classroom:board_draw')
        props.socket.off('classroom:board_image')
      }
    })
    
    // 监听Socket变化
    watch(() => props.socket, (newSocket, oldSocket) => {
      if (oldSocket) {
        oldSocket.off('classroom:board_draw')
        oldSocket.off('classroom:board_image')
      }
      if (newSocket) {
        newSocket.on('classroom:board_draw', receiveDrawing)
        newSocket.on('classroom:board_image', (data) => {
          setBackgroundImage(data.imageUrl)
        })
      }
    })
    
    return {
      // Refs
      mainCanvas,
      tempCanvas,
      imageInput,
      textInput,
      
      // State
      currentTool,
      currentColor,
      customColor,
      brushSize,
      showColorPicker,
      backgroundImage,
      zoomLevel,
      isTextEditing,
      textContent,
      
      // Computed
      canUndo,
      canRedo,
      textInputStyle,
      colorPalette,
      
      // Methods
      setTool,
      selectColor,
      handleMouseDown,
      handleMouseMove,
      handleMouseUp,
      handleTouchStart,
      handleTouchMove,
      handleTouchEnd,
      finishTextInput,
      cancelTextInput,
      undo,
      redo,
      clearCanvas,
      triggerImageUpload,
      handleImageUpload,
      onBackgroundLoad,
      downloadCanvas,
      zoomIn,
      zoomOut,
      resetZoom,
      setBackgroundImage,
      receiveDrawing
    }
  }
}
</script>

<style scoped>
.whiteboard-container {
  display: flex;
  flex: 1;
  min-height: 0;
  background: #f8f9fa;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 左侧工具栏 */
.toolbar-left {
  width: 72px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 12px 8px;
  gap: 8px;
  overflow-y: auto;
  flex-shrink: 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.toolbar-left::-webkit-scrollbar {
  width: 4px;
}

.toolbar-left::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.toolbar-left::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

.tool-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.tool-group:last-child {
  border-bottom: none;
}

.tool-group-label {
  font-size: 10px;
  color: var(--text-tertiary);
  text-align: center;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tool-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 8px 4px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.tool-btn.active {
  background: #409EFF;
  color: #fff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
}

.tool-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.tool-btn svg {
  width: 20px;
  height: 20px;
}

.tool-label {
  font-size: 9px;
  white-space: nowrap;
}

/* 颜色选择器 */
.color-picker-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
}

.color-preview {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: transform 0.2s;
}

.color-preview:hover {
  transform: scale(1.1);
}

.color-palette {
  position: absolute;
  left: 100%;
  top: 0;
  margin-left: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  padding: 8px;
  border-radius: var(--radius-md);
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  box-shadow: var(--shadow-lg);
  z-index: 100;
}

.color-swatch {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.color-swatch:hover {
  transform: scale(1.1);
}

.color-swatch.active {
  border-color: #409EFF;
  border-radius: 8px;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.custom-color-input {
  grid-column: span 5;
  width: 100%;
  height: 28px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 4px;
}

/* 大小控制 */
.size-control {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.size-preview {
  background: #fff;
  border-radius: 50%;
  min-width: 4px;
  min-height: 4px;
}

.size-slider {
  writing-mode: vertical-lr;
  direction: rtl;
  width: 20px;
  height: 60px;
  cursor: pointer;
}

.size-value {
  font-size: 10px;
  color: var(--text-tertiary);
}

/* 画布区域 */
.canvas-area {
  flex: 1;
  position: relative;
  background: #fff;
  overflow: hidden;
  min-height: 300px;
}

.canvas-area.readonly {
  cursor: default;
}

.canvas-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
  z-index: 1;
}

.main-canvas,
.temp-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.main-canvas {
  z-index: 2;
  cursor: crosshair;
}

.temp-canvas {
  z-index: 3;
  pointer-events: none;
}

.text-input {
  position: absolute;
  z-index: 10;
  border: 2px dashed #409eff;
  background: rgba(255, 255, 255, 0.9);
  padding: 4px 8px;
  outline: none;
  resize: none;
  min-width: 100px;
  min-height: 30px;
  font-family: Arial, sans-serif;
  border-radius: 4px;
}

.readonly-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 20;
}

.readonly-hint {
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
}

/* 缩放控制 */
.zoom-controls {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.95);
  padding: 6px 12px;
  border-radius: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.zoom-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all 0.2s;
}

.zoom-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.zoom-value {
  font-size: 12px;
  color: #666;
  min-width: 40px;
  text-align: center;
}
</style>
