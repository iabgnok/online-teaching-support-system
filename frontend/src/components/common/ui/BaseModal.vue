<template>
  <Teleport to="body">
    <div v-if="visible" class="base-modal-overlay" @click="handleOverlayClick">
      <div class="base-modal" :class="modalClass" @click.stop>
        <div class="base-modal-header" v-if="title || $slots.header">
          <slot name="header">
            <h3 class="base-modal-title">{{ title }}</h3>
          </slot>
          <button v-if="closable" class="base-modal-close" @click="handleClose">
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <div class="base-modal-body">
          <slot></slot>
        </div>
        <div class="base-modal-footer" v-if="$slots.footer">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
export default {
  name: 'BaseModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: ''
    },
    width: {
      type: [String, Number],
      default: '500px'
    },
    closable: {
      type: Boolean,
      default: true
    },
    maskClosable: {
      type: Boolean,
      default: true
    },
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large', 'fullscreen'].includes(value)
    }
  },
  emits: ['update:visible', 'close'],
  computed: {
    modalClass() {
      return [
        'base-modal',
        `base-modal--${this.size}`
      ]
    },
    modalStyle() {
      return {
        width: typeof this.width === 'number' ? `${this.width}px` : this.width
      }
    }
  },
  methods: {
    handleClose() {
      this.$emit('update:visible', false)
      this.$emit('close')
    },
    handleOverlayClick() {
      if (this.maskClosable) {
        this.handleClose()
      }
    }
  }
}
</script>

<style scoped>
.base-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.base-modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.base-modal--small {
  width: 300px;
}

.base-modal--medium {
  width: 500px;
}

.base-modal--large {
  width: 800px;
}

.base-modal--fullscreen {
  width: 95vw;
  height: 95vh;
}

.base-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
}

.base-modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.base-modal-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.base-modal-close:hover {
  background-color: #f5f5f5;
}

.base-modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.base-modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>