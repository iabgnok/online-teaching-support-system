<template>
  <div class="whiteboard-container">
    <!-- 左侧工具栏 -->
    <div class="toolbar-left" :class="{ 'readonly': readonly }">
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
      <!-- 画布包装器 (承载位移和缩放) -->
      <div 
        class="canvas-wrapper" 
        :style="{
          transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`,
          transformOrigin: '0 0'
        }"
      >
        <!-- 画板视口 (Viewport) -->
        <div class="whiteboard-viewport">
          <!-- 背景图片层 -->
          <img 
            v-if="backgroundImage" 
            :src="backgroundImage" 
            class="canvas-background"
            @load="onBackgroundLoad"
          />
          
          <!-- 画布变换容器 (只包含画布，不包含其他UI) -->
          <div 
            class="canvas-transform-wrapper"
            :style="canvasTransformStyle"
          >
            <!-- 主画布 -->
            <canvas
              ref="mainCanvas"
              class="main-canvas"
              @mousedown="handleMouseDown"
              @mousemove="handleMouseMove"
              @mouseup="handleMouseUp"
              @mouseleave="handleMouseUp"
              @wheel="handleWheel"
              @contextmenu.prevent="handleContextMenu"
            ></canvas>
            
            <!-- 临时画布（用于形状预览） -->
            <canvas
              ref="tempCanvas"
              class="temp-canvas"
            ></canvas>
          </div>
          
          <!-- 文本输入框 (不随画布变换) -->
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
        </div>
      </div>
      
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
      <span class="zoom-value">{{ Math.round(scale * 100) }}%</span>
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
    // 存储正在接收的分段 stroke 的最后一点
    const strokeLastPointMap = {}
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
    
    // 视口变换参数
    const offsetX = ref(0)
    const offsetY = ref(0)
    const scale = ref(1)
    
    // 绘制状态
    const isDrawing = ref(false)
    const isPanning = ref(false) // 新增：是否正在平移
    const startPoint = reactive({ x: 0, y: 0 })
    const lastPoint = reactive({ x: 0, y: 0 })
    const panStartPoint = reactive({ x: 0, y: 0 }) // 新增：平移开始点
    
    // 文本输入
    const isTextEditing = ref(false)
    const textContent = ref('')
    const textPosition = reactive({ x: 0, y: 0 })
    
    // 历史记录（用于撤销/重做）
    const history = ref([])
    const historyIndex = ref(-1)
    const maxHistory = 50

    // 画笔缓冲与批量发送设置：用于减少丢帧时的断裂（快速绘制时聚合点并插值）
    const strokeBuffer = ref([])
    const currentStrokeId = ref(null)
    let strokeFlushTimer = null
    const STROKE_FLUSH_INTERVAL = 40 // ms
    const STROKE_MAX_POINTS = 6
    
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
      left: (textPosition.x * scale.value + offsetX.value) + 'px',
      top: (textPosition.y * scale.value + offsetY.value) + 'px',
      color: currentColor.value,
      fontSize: (brushSize.value * 4 * scale.value) + 'px',
      transform: `scale(${1/scale.value})`,
      transformOrigin: 'top left'
    }))
    
    const canvasTransformStyle = computed(() => ({
      // 变换已移至canvas-wrapper，这里不再需要
      transform: 'none'
    }))
    
    // ========== Canvas Context ==========
    let ctx = null
    let tempCtx = null
    
    // ========== Methods ==========
    const initCanvas = () => {
      if (!mainCanvas.value || !tempCanvas.value) {
        // 如果 canvas 元素还没有准备好，延迟重试
        setTimeout(() => {
          if (!ctx) initCanvas()
        }, 100)
        return
      }
      
      ctx = mainCanvas.value.getContext('2d', { willReadFrequently: true })
      tempCtx = tempCanvas.value.getContext('2d', { willReadFrequently: true })
      
      // 设置固定的逻辑分辨率，不再随窗口变化
      mainCanvas.value.width = 1920
      mainCanvas.value.height = 1080
      tempCanvas.value.width = 1920
      tempCanvas.value.height = 1080
      
      // 重新设置画布样式
      if (ctx) {
        ctx.lineCap = 'round'
        ctx.lineJoin = 'round'
      }
      
      // 保存初始状态
      saveHistory()
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
      if (!mainCanvas.value) return { x: 0, y: 0 }

      // 获取whiteboard-container的边界作为视口
      const whiteboardRef = mainCanvas.value.closest('.whiteboard-container')
      if (!whiteboardRef) return { x: 0, y: 0 }
      
      const rect = whiteboardRef.getBoundingClientRect()
      const clientX = e.touches ? e.touches[0].clientX : e.clientX
      const clientY = e.touches ? e.touches[0].clientY : e.clientY
      
      // 1. 计算鼠标相对于视口左上角的距离
      const xInViewport = clientX - rect.left
      const yInViewport = clientY - rect.top

      // 2. 减去偏移量，再除以缩放比例，得到画布上的绝对坐标
      const logicalX = (xInViewport - offsetX.value) / scale.value
      const logicalY = (yInViewport - offsetY.value) / scale.value
      
      return { x: logicalX, y: logicalY }
    }
    
    const handleMouseDown = (e) => {
      if (props.readonly || !ctx) return

      // 检查是否为右键点击（平移模式）
      if (e.button === 2) {
        isPanning.value = true
        panStartPoint.x = e.clientX - offsetX.value
        panStartPoint.y = e.clientY - offsetY.value
        mainCanvas.value.style.cursor = 'grabbing'
        return
      }

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

      // 初始化当前 stroke
      strokeBuffer.value = []
      currentStrokeId.value = `${Date.now()}-${Math.random().toString(36).slice(2,7)}`
      // 添加起始点
      addPointToStroke(point)

      // 自由绘制工具立即开始绘制
      if (['pen', 'highlighter', 'eraser'].includes(currentTool.value)) {
        beginPath(point)
      }
    }
    
    const handleMouseMove = (e) => {
      // 处理平移
      if (isPanning.value) {
        offsetX.value = e.clientX - panStartPoint.x
        offsetY.value = e.clientY - panStartPoint.y
        return
      }

      if (!isDrawing.value || props.readonly || !ctx) return

      const point = getEventPoint(e)

      if (['pen', 'highlighter', 'eraser'].includes(currentTool.value)) {
        // 自由绘制（本地即时渲染）
        drawLine(lastPoint, point)

        // 缓存并批量发送到服务器，提高快速绘制时的连贯性
        addPointToStroke(point)

        lastPoint.x = point.x
        lastPoint.y = point.y
      } else {
        // 形状预览
        drawShapePreview(point)
        // 发送 shape preview 到学生端（节流）
        emitShapePreview(startPoint, point)
      }
    }
    
    const handleMouseUp = (e) => {
      // 结束平移模式
      if (isPanning.value) {
        isPanning.value = false
        mainCanvas.value.style.cursor = 'crosshair'
        return
      }

      if (!isDrawing.value || props.readonly) return

      const point = getEventPoint(e)

      // 形状工具完成绘制
      if (['line', 'arrow', 'rect', 'circle'].includes(currentTool.value)) {
        drawShape(startPoint, point)
        clearTempCanvas()

        // 发送形状到服务器（最终形状）
        emitDrawing({
          type: 'shape',
          tool: currentTool.value,
          from: { ...startPoint },
          to: point,
          color: currentColor.value,
          size: brushSize.value
        })

        // 额外发送 shape_complete 以便学生能将形状固定到主画布
        emitShapeComplete(startPoint, point)
      }

      // 结束当前 stroke（确保最后的点被发送）
      isDrawing.value = false
      flushStroke(true)
      saveHistory()
    }
    
    const handleTouchStart = (e) => handleMouseDown(e)
    const handleTouchMove = (e) => handleMouseMove(e)
    const handleTouchEnd = (e) => handleMouseUp(e)
    
    const handleWheel = (e) => {
      if (props.readonly) return
      
      // Ctrl+滚轮缩放
      if (e.ctrlKey) {
        e.preventDefault() // 阻止浏览器默认的页面缩放
        const delta = e.deltaY > 0 ? -0.1 : 0.1
        handleZoomAtPoint(e.clientX, e.clientY, delta)
      }
    }
    
    const handleContextMenu = (e) => {
      // 右键菜单已通过 @contextmenu.prevent 阻止
      // 此函数为占位符，确保事件绑定正确
    }
    
    const beginPath = (point) => {
      if (!ctx) return
      
      ctx.beginPath()
      ctx.moveTo(point.x, point.y)
      applyToolStyle()
    }
    
    const applyToolStyle = () => {
      if (!ctx) return
      
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
      if (!ctx) return
      
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

    // ========== Stroke buffering & smoothing helpers ==========
    const addPointToStroke = (point) => {
      if (!mainCanvas.value) return
      const w = mainCanvas.value.width
      const h = mainCanvas.value.height
      strokeBuffer.value.push({ x_percent: point.x / w, y_percent: point.y / h, t: Date.now() })

      // 如果缓冲已满立刻发送
      if (strokeBuffer.value.length >= STROKE_MAX_POINTS) {
        flushStroke(false)
        return
      }

      // 定时发送（合并小段）
      if (!strokeFlushTimer) {
        strokeFlushTimer = setTimeout(() => {
          flushStroke(false)
        }, STROKE_FLUSH_INTERVAL)
      }
    }

    const flushStroke = (isEnd = false) => {
      if (!props.socket || strokeBuffer.value.length === 0) return

      const payload = {
        lesson_id: props.lessonId,
        stroke_id: currentStrokeId.value,
        tool: currentTool.value,
        color: currentColor.value,
        size: brushSize.value,
        points: strokeBuffer.value.slice(),
        isEnd: !!isEnd,
        created_at: Date.now()
      }

      props.socket.emit('classroom:board_stroke', payload)

      strokeBuffer.value = []
      if (strokeFlushTimer) { clearTimeout(strokeFlushTimer); strokeFlushTimer = null }
      if (isEnd) { currentStrokeId.value = null }
    }

    const drawStrokePoints = (points, tool, color, size, strokeId) => {
      if (!ctx || !mainCanvas.value || !points || points.length === 0) return
      const w = mainCanvas.value.width
      const h = mainCanvas.value.height

      // 将百分比转换为像素并密化（插值）以填补大间隔
      const pts = []
      for (let i = 0; i < points.length; i++) {
        const p = points[i]
        const x = (p.x_percent !== undefined) ? p.x_percent * w : (p.x || 0)
        const y = (p.y_percent !== undefined) ? p.y_percent * h : (p.y || 0)
        pts.push({ x, y })
      }

      // 如果有之前的末点（相同 strokeId），在首点前追加，以连接分段
      if (strokeId && strokeLastPointMap[strokeId]) {
        const prev = strokeLastPointMap[strokeId]
        const first = pts[0]
        const dx = first.x - prev.x
        const dy = first.y - prev.y
        const dist = Math.hypot(dx, dy)
        if (dist > 0.5) {
          // 插入 prev 到首点的中间点来避免断裂
          pts.unshift(prev)
        }
      }

      // 插值：如果相邻点距离过大，插入线性中间点
      const densified = []
      for (let i = 0; i < pts.length - 1; i++) {
        const a = pts[i]
        const b = pts[i + 1]
        densified.push(a)
        const dx = b.x - a.x
        const dy = b.y - a.y
        const dist = Math.hypot(dx, dy)
        const step = Math.max(0, Math.floor(dist / Math.max(2, size * 2)))
        for (let s = 1; s < step; s++) {
          const t = s / step
          densified.push({ x: a.x + dx * t, y: a.y + dy * t })
        }
      }
      densified.push(pts[pts.length - 1])

      // 绘制平滑曲线
      ctx.save()
      ctx.strokeStyle = color
      ctx.lineWidth = size
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      ctx.globalCompositeOperation = (tool === 'eraser') ? 'destination-out' : 'source-over'
      if (tool === 'highlighter') ctx.globalAlpha = 0.3

      if (densified.length === 1) {
        const p = densified[0]
        ctx.beginPath()
        ctx.arc(p.x, p.y, Math.max(1, size / 2), 0, Math.PI * 2)
        ctx.fillStyle = color
        if (tool === 'eraser') { ctx.globalCompositeOperation = 'destination-out'; ctx.fill(); ctx.globalCompositeOperation = 'source-over' } else { ctx.fill() }
      } else {
        ctx.beginPath()
        ctx.moveTo(densified[0].x, densified[0].y)
        for (let i = 1; i < densified.length; i++) {
          const prev = densified[i - 1]
          const cur = densified[i]
          const cx = (prev.x + cur.x) / 2
          const cy = (prev.y + cur.y) / 2
          ctx.quadraticCurveTo(prev.x, prev.y, cx, cy)
        }
        // 到最后一点
        const last = densified[densified.length - 1]
        ctx.lineTo(last.x, last.y)
        ctx.stroke()

        // 在端点填充圆点以避免断点
        const radius = Math.max(1, size / 2)
        ctx.beginPath()
        ctx.arc(last.x, last.y, radius, 0, Math.PI * 2)
        ctx.fillStyle = color
        if (tool === 'eraser') { ctx.globalCompositeOperation = 'destination-out'; ctx.fill(); ctx.globalCompositeOperation = 'source-over' } else { ctx.fill() }
      }

      ctx.restore()

      // 更新 stroke 最后点（用于连接下一段）
      if (strokeId) {
        strokeLastPointMap[strokeId] = pts[pts.length - 1]
        if (points.length && points[points.length - 1].isEnd) {
          delete strokeLastPointMap[strokeId]
        }
      }
    }

    const receiveStroke = (data) => {
      if (!data || !data.points) return

      // 忽略在清空之前发生的 stroke（基于点时间戳）
      const maxT = Math.max(...data.points.map(p => p.t || 0))
      if (lastClearTimestamp.value && maxT <= lastClearTimestamp.value) {
        return
      }

      drawStrokePoints(data.points, data.tool || 'pen', data.color || '#000', data.size || 3, data.stroke_id)

      // 如果此段为结束，则记录历史以便撤销/重做
      if (data.isEnd) saveHistory()

      // 如果 stroke 带有 isEnd 并且清除了之前临时预览，我们应该确保临时画布清空
      if (data.isEnd) clearTempCanvas()
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

      // 先取消并清空正在缓冲的 stroke，防止清空后缓冲数据被发送回来
      strokeBuffer.value = []
      if (strokeFlushTimer) { clearTimeout(strokeFlushTimer); strokeFlushTimer = null }
      currentStrokeId.value = null

      // 清空主画布与临时画布
      ctx.clearRect(0, 0, mainCanvas.value.width, mainCanvas.value.height)
      clearTempCanvas()
      saveHistory()

      // 广播清空事件
      if (props.socket) {
        props.socket.emit('classroom:board_clear', { lesson_id: props.lessonId, cleared_at: Date.now() })
      }
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

    // 记录最近一次被清空的时间戳，用于忽略清空前的延迟数据
    const lastClearTimestamp = ref(0)

    // ========== Shape preview (remote & local emission) ==========
    const shapePreviewThrottleTimer = { timer: null }
    const SHAPE_PREVIEW_INTERVAL = 50 // ms

    const emitShapePreview = (from, to) => {
      if (!props.socket || !mainCanvas.value) return
      const w = mainCanvas.value.width
      const h = mainCanvas.value.height
      const payload = {
        lesson_id: props.lessonId,
        tool: currentTool.value,
        color: currentColor.value,
        size: brushSize.value,
        from_percent: { x: from.x / w, y: from.y / h },
        to_percent: { x: to.x / w, y: to.y / h }
      }
      // throttle
      if (shapePreviewThrottleTimer.timer) return
      shapePreviewThrottleTimer.timer = setTimeout(() => { shapePreviewThrottleTimer.timer = null }, SHAPE_PREVIEW_INTERVAL)
      props.socket.emit('classroom:shape_preview', payload)
    }

    const emitShapeComplete = (from, to) => {
      if (!props.socket || !mainCanvas.value) return
      const w = mainCanvas.value.width
      const h = mainCanvas.value.height
      const payload = {
        lesson_id: props.lessonId,
        tool: currentTool.value,
        color: currentColor.value,
        size: brushSize.value,
        from_percent: { x: from.x / w, y: from.y / h },
        to_percent: { x: to.x / w, y: to.y / h }
      }
      props.socket.emit('classroom:shape_complete', payload)
    }

    // Draw preview on temp canvas for remote shapes
    const renderRemoteShapePreview = (from, to, tool, color, size) => {
      if (!tempCtx || !tempCanvas.value) return
      clearTempCanvas()
      tempCtx.strokeStyle = color || '#000'
      tempCtx.lineWidth = size || 3
      tempCtx.lineCap = 'round'
      tempCtx.lineJoin = 'round'
      tempCtx.globalCompositeOperation = (tool === 'eraser') ? 'destination-out' : 'source-over'

      // draw same shapes as local preview
      tempCtx.beginPath()
      switch ((tool || 'line')) {
        case 'line':
          tempCtx.moveTo(from.x, from.y)
          tempCtx.lineTo(to.x, to.y)
          tempCtx.stroke()
          break
        case 'arrow':
          drawArrow(tempCtx, from, to)
          tempCtx.stroke()
          break
        case 'rect':
          tempCtx.rect(from.x, from.y, to.x - from.x, to.y - from.y)
          tempCtx.stroke()
          break
        case 'circle':
          const rx = Math.abs(to.x - from.x) / 2
          const ry = Math.abs(to.y - from.y) / 2
          const cx = from.x + (to.x - from.x) / 2
          const cy = from.y + (to.y - from.y) / 2
          tempCtx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2)
          tempCtx.stroke()
          break
      }
    }

    const handleRemoteShapeComplete = (from, to, tool, color, size) => {
      // Draw final shape on main canvas
      if (!ctx) return
      ctx.save()
      ctx.strokeStyle = color || '#000'
      ctx.lineWidth = size || 3
      ctx.globalCompositeOperation = (tool === 'eraser') ? 'destination-out' : 'source-over'
      drawShape(from, to)
      ctx.restore()
      clearTempCanvas()
    }
    
    // 下载
    const downloadCanvas = () => {
      const link = document.createElement('a')
      link.download = `whiteboard_${props.lessonId}_${Date.now()}.png`
      link.href = mainCanvas.value.toDataURL()
      link.click()
    }
    
    // 缩放
    const handleZoomAtPoint = (clientX, clientY, delta) => {
      // 获取whiteboard-container的边界作为视口
      const whiteboardRef = mainCanvas.value.closest('.whiteboard-container')
      if (!whiteboardRef) return
      
      const rect = whiteboardRef.getBoundingClientRect()
      const viewportX = clientX - rect.left
      const viewportY = clientY - rect.top
      
      // 计算缩放前的画布坐标
      const oldScale = scale.value
      const canvasX = (viewportX - offsetX.value) / oldScale
      const canvasY = (viewportY - offsetY.value) / oldScale
      
      // 应用缩放
      const newScale = Math.max(0.1, Math.min(5, oldScale + delta))
      scale.value = newScale
      
      // 调整偏移以保持缩放中心点不变
      offsetX.value = viewportX - canvasX * newScale
      offsetY.value = viewportY - canvasY * newScale
    }
    
    const zoomIn = () => {
      scale.value = Math.min(scale.value + 0.1, 3)
    }
    
    const zoomOut = () => {
      scale.value = Math.max(scale.value - 0.1, 0.5)
    }
    
    const resetZoom = () => {
      scale.value = 1
      offsetX.value = 0
      offsetY.value = 0
    }
    
    // Socket通信
    const emitDrawing = (data) => {
      if (!props.socket || !mainCanvas.value) return

      // 拓展为发送相对（百分比）坐标，便于不同尺寸浏览器同步
      const payload = {
        lesson_id: props.lessonId,
        ...data
      }

      if (data.from) {
        payload.from_percent = {
          x: data.from.x / mainCanvas.value.width,
          y: data.from.y / mainCanvas.value.height
        }
      }
      if (data.to) {
        payload.to_percent = {
          x: data.to.x / mainCanvas.value.width,
          y: data.to.y / mainCanvas.value.height
        }
      }

      // 文本位置也使用百分比
      if (data.position) {
        payload.position_percent = {
          x: data.position.x / mainCanvas.value.width,
          y: data.position.y / mainCanvas.value.height
        }
      }

      // 图片使用百分比表示位置与尺寸
      if (data.x !== undefined && data.y !== undefined && data.width !== undefined && data.height !== undefined) {
        payload.x_percent = data.x / mainCanvas.value.width
        payload.y_percent = data.y / mainCanvas.value.height
        payload.width_percent = data.width / mainCanvas.value.width
        payload.height_percent = data.height / mainCanvas.value.height
      }

      props.socket.emit('classroom:board_draw', payload)

      emit('board-updated', data)
    }
    
    const receiveDrawing = (data) => {
      if (!ctx || !mainCanvas.value) return

      // helper: convert percent coords (来自不同尺寸画布) 为当前画布像素坐标
      const mainW = mainCanvas.value.width
      const mainH = mainCanvas.value.height

      const from = data.from_percent ? {
        x: data.from_percent.x * mainW,
        y: data.from_percent.y * mainH
      } : data.from

      const to = data.to_percent ? {
        x: data.to_percent.x * mainW,
        y: data.to_percent.y * mainH
      } : data.to

      // 确保圆角、平滑连接
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'

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

          if (from && to) {
            // 使用二次曲线平滑线段，减少离散点的断裂感
            ctx.beginPath()
            ctx.moveTo(from.x, from.y)
            const cx = (from.x + to.x) / 2
            const cy = (from.y + to.y) / 2
            ctx.quadraticCurveTo(cx, cy, to.x, to.y)
            ctx.stroke()

            // 在端点填充圆点以覆盖间隙
            const radius = Math.max(1, data.size / 2)
            ctx.beginPath()
            ctx.arc(to.x, to.y, radius, 0, Math.PI * 2)
            ctx.fillStyle = data.color
            if (data.tool === 'eraser') {
              // 用擦除模式清除圆点
              ctx.globalCompositeOperation = 'destination-out'
              ctx.fill()
              ctx.globalCompositeOperation = 'source-over'
            } else {
              ctx.fill()
            }
          }

          ctx.globalAlpha = 1
          break

        case 'shape':
          if (from && to) drawShape(from, to)
          break

        case 'text':
          const pos = data.position && data.position.x !== undefined && data.position.y !== undefined
            ? (data.position_percent ? { x: data.position_percent.x * mainW, y: data.position_percent.y * mainH } : data.position)
            : null
          if (pos) {
            ctx.font = `${data.size}px Arial`
            ctx.fillStyle = data.color
            ctx.fillText(data.content, pos.x, pos.y + data.size)
          }
          break

        case 'clear':
          // 兼容旧的 clear 事件
          const clearedAt = Date.now()
          lastClearTimestamp.value = clearedAt
          ctx.clearRect(0, 0, mainCanvas.value.width, mainCanvas.value.height)
          clearTempCanvas()
          strokeBuffer.value = []
          if (strokeFlushTimer) { clearTimeout(strokeFlushTimer); strokeFlushTimer = null }
          currentStrokeId.value = null
          for (const k of Object.keys(strokeLastPointMap)) delete strokeLastPointMap[k]
          // 记录空白状态
          saveHistory()
          break

        case 'image':
          const img = new Image()
          img.onload = () => {
            // 支持百分比坐标
            const x = data.x_percent !== undefined ? data.x_percent * mainW : data.x
            const y = data.y_percent !== undefined ? data.y_percent * mainH : data.y
            const width = data.width_percent !== undefined ? data.width_percent * mainW : data.width
            const height = data.height_percent !== undefined ? data.height_percent * mainH : data.height
            ctx.drawImage(img, x, y, width, height)
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
    watch([mainCanvas, tempCanvas], ([newMain, newTemp]) => {
      if (newMain && newTemp && !ctx) {
        initCanvas()
      }
    }, { immediate: true })
    
    onMounted(() => {
      // 额外延迟确保 DOM 完全准备好
      setTimeout(() => {
        if (!ctx) initCanvas()
      }, 200)
      window.addEventListener('keydown', handleKeyDown)

      // 监听Socket事件
      if (props.socket) {
        props.socket.on('classroom:board_draw', receiveDrawing)
        props.socket.on('classroom:board_image', (data) => {
          setBackgroundImage(data.imageUrl)
        })

        // 新的批量 stroke 协议
        props.socket.on('classroom:board_stroke', receiveStroke)

        // board clear
        props.socket.on('classroom:board_clear', (payload) => {
          lastClearTimestamp.value = payload?.cleared_at || Date.now()
          // 清空主画布和临时画布、重置状态
          if (ctx && mainCanvas.value) ctx.clearRect(0, 0, mainCanvas.value.width, mainCanvas.value.height)
          clearTempCanvas()
          strokeBuffer.value = []
          if (strokeFlushTimer) { clearTimeout(strokeFlushTimer); strokeFlushTimer = null }
          currentStrokeId.value = null
          // 清除记录的分段最后点
          for (const k of Object.keys(strokeLastPointMap)) delete strokeLastPointMap[k]
          // 记录空白状态到历史，便于撤销/重做
          saveHistory()
        })

        // shape preview / complete
        props.socket.on('classroom:shape_preview', (payload) => {
          if (!mainCanvas.value || !tempCanvas.value) return
          const w = mainCanvas.value.width
          const h = mainCanvas.value.height
          const from = { x: payload.from_percent.x * w, y: payload.from_percent.y * h }
          const to = { x: payload.to_percent.x * w, y: payload.to_percent.y * h }
          renderRemoteShapePreview(from, to, payload.tool, payload.color, payload.size)
        })
        props.socket.on('classroom:shape_complete', (payload) => {
          if (!mainCanvas.value) return
          const w = mainCanvas.value.width
          const h = mainCanvas.value.height
          const from = { x: payload.from_percent.x * w, y: payload.from_percent.y * h }
          const to = { x: payload.to_percent.x * w, y: payload.to_percent.y * h }
          handleRemoteShapeComplete(from, to, payload.tool, payload.color, payload.size)
          // 记录历史，保证后续 undo/redo 正确
          saveHistory()
        })

        // 兼容旧版 drawing 协议（normalized prevX/x 等）
        props.socket.on('drawing_update', (data) => {
          if (!mainCanvas.value) return
          const w = mainCanvas.value.width
          const h = mainCanvas.value.height
          const from = {
            x: (data.prevX !== undefined ? data.prevX : data.from?.x) * w,
            y: (data.prevY !== undefined ? data.prevY : data.from?.y) * h
          }
          const to = {
            x: (data.x !== undefined ? data.x : data.to?.x) * w,
            y: (data.y !== undefined ? data.y : data.to?.y) * h
          }
          const drawData = {
            type: 'draw',
            tool: data.action || data.tool,
            color: data.color,
            size: data.brush_size || data.size,
            from,
            to
          }
          receiveDrawing(drawData)
        })
      }
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', resizeCanvas)
      window.removeEventListener('keydown', handleKeyDown)

      if (props.socket) {
        props.socket.off('classroom:board_draw')
        props.socket.off('classroom:board_image')
        props.socket.off('drawing_update')
        props.socket.off('classroom:board_stroke')
        props.socket.off('classroom:shape_preview')
        props.socket.off('classroom:shape_complete')
      }
    })

    // 监听Socket变化
    watch(() => props.socket, (newSocket, oldSocket) => {
      if (oldSocket) {
        oldSocket.off('classroom:board_draw')
        oldSocket.off('classroom:board_image')
        oldSocket.off('drawing_update')
        oldSocket.off('classroom:board_stroke')
        oldSocket.off('classroom:shape_preview')
        oldSocket.off('classroom:shape_complete')
      }
      if (newSocket) {
        newSocket.on('classroom:board_draw', receiveDrawing)
        newSocket.on('classroom:board_image', (data) => {
          setBackgroundImage(data.imageUrl)
        })
        newSocket.on('classroom:board_stroke', receiveStroke)
        newSocket.on('classroom:shape_preview', (payload) => {
          if (!mainCanvas.value || !tempCanvas.value) return
          const w = mainCanvas.value.width
          const h = mainCanvas.value.height
          const from = { x: payload.from_percent.x * w, y: payload.from_percent.y * h }
          const to = { x: payload.to_percent.x * w, y: payload.to_percent.y * h }
          renderRemoteShapePreview(from, to, payload.tool, payload.color, payload.size)
        })
        newSocket.on('classroom:shape_complete', (payload) => {
          if (!mainCanvas.value) return
          const w = mainCanvas.value.width
          const h = mainCanvas.value.height
          const from = { x: payload.from_percent.x * w, y: payload.from_percent.y * h }
          const to = { x: payload.to_percent.x * w, y: payload.to_percent.y * h }
          handleRemoteShapeComplete(from, to, payload.tool, payload.color, payload.size)
        })
        newSocket.on('drawing_update', (data) => {
          if (!mainCanvas.value) return
          const w = mainCanvas.value.width
          const h = mainCanvas.value.height
          const from = {
            x: (data.prevX !== undefined ? data.prevX : data.from?.x) * w,
            y: (data.prevY !== undefined ? data.prevY : data.from?.y) * h
          }
          const to = {
            x: (data.x !== undefined ? data.x : data.to?.x) * w,
            y: (data.y !== undefined ? data.y : data.to?.y) * h
          }
          const drawData = {
            type: 'draw',
            tool: data.action || data.tool,
            color: data.color,
            size: data.brush_size || data.size,
            from,
            to
          }
          receiveDrawing(drawData)
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
      scale,
      offsetX,
      offsetY,
      isTextEditing,
      textContent,
      
      // Computed
      canUndo,
      canRedo,
      textInputStyle,
      canvasTransformStyle, // 新增：画布变换样式
      colorPalette,
      
      // Methods
      setTool,
      selectColor,
      getEventPoint,
      handleMouseDown,
      handleMouseMove,
      handleMouseUp,
      handleWheel,
      handleContextMenu, // 新增：右键菜单处理
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
      handleZoomAtPoint, // 新增：指定点缩放
      zoomIn,
      zoomOut,
      resetZoom,
      setBackgroundImage,
      receiveDrawing,
      // new helpers
      receiveStroke,
      emitShapePreview,
      emitShapeComplete,
      renderRemoteShapePreview
    }
  }
}
</script>

<style scoped>
.whiteboard-container {
  position: relative;
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
  flex-shrink: 0;
  width: 72px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 12px 8px;
  gap: 8px;
  overflow-y: auto;
  z-index: 10; /* 工具栏最高层级，悬浮在视口之上 */
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.toolbar-left::-webkit-scrollbar {
  width: 4px;
}

.toolbar-left::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.toolbar-left.readonly {
  opacity: 0.5;
  pointer-events: none;
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
  background: #f9f7f7; /* 深灰色背景，表示画布外区域 */
  overflow: hidden;
  min-height: 300px;
}

.canvas-area.readonly {
  cursor: default;
}

/* 画板视口 (Viewport) */
.whiteboard-viewport {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #5d5c5c; /* 画布区域为白色 */
  z-index: 5; /* 视口层级 */
}

/* 画布变换容器 (只包含画布，不包含其他UI) */
.canvas-transform-wrapper {
  position: relative;
  width: 1920px;  /* 必须与逻辑宽度一致 */
  height: 1080px; /* 必须与逻辑高度一致 */
  transform-origin: top left;
  background: #f9f7f7;
  z-index: 2; /* 画布层级 */
}

.canvas-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
  z-index: 1; /* 背景层级 */
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
  z-index: 1; /* 相对于canvas-container */
  cursor: crosshair;
}

.temp-canvas {
  z-index: 2; /* 临时画布在主画布之上 */
  pointer-events: none;
}

.text-input {
  position: absolute;
  z-index: 5; /* 相对于canvas-container，文本输入在画布之上 */
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
