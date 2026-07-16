<template>
  <div>
    <label v-if="label" class="block text-sm font-medium text-slate-700 mb-1.5">{{ label }}</label>
    <select
      v-if="type === 'select'"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      class="app-input"
      :required="required"
    >
      <option value="">{{ placeholder || '— Sélectionner —' }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
    <textarea
      v-else-if="type === 'textarea'"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      :rows="rows"
      class="app-input resize-y min-h-[88px]"
      :placeholder="placeholder"
      :required="required"
    />
    <input
      v-else
      :type="type"
      :value="modelValue"
      @input="$emit('update:modelValue', type === 'number' ? Number($event.target.value) : $event.target.value)"
      class="app-input"
      :placeholder="placeholder"
      :required="required"
      :min="min"
      :step="step"
    />
  </div>
</template>

<script setup>
defineProps({
  label: String,
  modelValue: [String, Number],
  type: { type: String, default: 'text' },
  placeholder: String,
  required: Boolean,
  options: { type: Array, default: () => [] },
  rows: { type: Number, default: 3 },
  min: String,
  step: String,
})
defineEmits(['update:modelValue'])
</script>
