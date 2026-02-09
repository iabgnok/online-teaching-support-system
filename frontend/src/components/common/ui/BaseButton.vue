<template>
  <button
    :class="buttonClass"
    :disabled="disabled"
    @click="handleClick"
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  name: 'BaseButton',
  props: {
    type: {
      type: String,
      default: 'primary',
      validator: value => ['primary', 'secondary', 'success', 'danger', 'warning'].includes(value)
    },
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large'].includes(value)
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    buttonClass() {
      return [
        'base-button',
        `base-button--${this.type}`,
        `base-button--${this.size}`,
        {
          'base-button--disabled': this.disabled,
          'base-button--loading': this.loading
        }
      ]
    }
  },
  methods: {
    handleClick(event) {
      if (!this.disabled && !this.loading) {
        this.$emit('click', event)
      }
    }
  }
}
</script>

<style scoped>
.base-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
}

.base-button--primary {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.base-button--primary:hover:not(.base-button--disabled) {
  background-color: #0056b3;
  border-color: #0056b3;
}

.base-button--secondary {
  background-color: #6c757d;
  color: white;
  border-color: #6c757d;
}

.base-button--secondary:hover:not(.base-button--disabled) {
  background-color: #545b62;
  border-color: #545b62;
}

.base-button--success {
  background-color: #28a745;
  color: white;
  border-color: #28a745;
}

.base-button--success:hover:not(.base-button--disabled) {
  background-color: #1e7e34;
  border-color: #1e7e34;
}

.base-button--danger {
  background-color: #dc3545;
  color: white;
  border-color: #dc3545;
}

.base-button--danger:hover:not(.base-button--disabled) {
  background-color: #bd2130;
  border-color: #bd2130;
}

.base-button--warning {
  background-color: #ffc107;
  color: #212529;
  border-color: #ffc107;
}

.base-button--warning:hover:not(.base-button--disabled) {
  background-color: #e0a800;
  border-color: #e0a800;
}

.base-button--small {
  padding: 4px 8px;
  font-size: 12px;
}

.base-button--large {
  padding: 12px 24px;
  font-size: 16px;
}

.base-button--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.base-button--loading {
  cursor: not-allowed;
}
</style>