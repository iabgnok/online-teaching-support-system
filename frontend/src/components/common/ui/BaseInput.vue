<template>
  <div class="base-input-wrapper">
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :maxlength="maxlength"
      :class="inputClass"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
      ref="inputRef"
    />
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script>
export default {
  name: 'BaseInput',
  props: {
    modelValue: {
      type: [String, Number],
      default: ''
    },
    type: {
      type: String,
      default: 'text'
    },
    placeholder: {
      type: String,
      default: ''
    },
    disabled: {
      type: Boolean,
      default: false
    },
    readonly: {
      type: Boolean,
      default: false
    },
    maxlength: {
      type: Number,
      default: null
    },
    error: {
      type: String,
      default: ''
    },
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large'].includes(value)
    }
  },
  emits: ['update:modelValue', 'blur', 'focus'],
  computed: {
    inputClass() {
      return [
        'base-input',
        `base-input--${this.size}`,
        {
          'base-input--error': this.error,
          'base-input--disabled': this.disabled
        }
      ]
    }
  },
  methods: {
    handleInput(event) {
      this.$emit('update:modelValue', event.target.value)
    },
    handleBlur(event) {
      this.$emit('blur', event)
    },
    handleFocus(event) {
      this.$emit('focus', event)
    },
    focus() {
      this.$refs.inputRef.focus()
    }
  }
}
</script>

<style scoped>
.base-input-wrapper {
  position: relative;
}

.base-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s ease;
  outline: none;
}

.base-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.base-input--small {
  padding: 4px 8px;
  font-size: 12px;
}

.base-input--large {
  padding: 12px 16px;
  font-size: 16px;
}

.base-input--error {
  border-color: #dc3545;
}

.base-input--error:focus {
  border-color: #dc3545;
  box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.25);
}

.base-input--disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.error-message {
  color: #dc3545;
  font-size: 12px;
  margin-top: 4px;
}
</style>