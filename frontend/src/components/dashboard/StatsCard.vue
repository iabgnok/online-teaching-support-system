<template>
  <div class="stats-card">
    <div class="icon">
      <i :class="iconClass"></i>
    </div>
    <div class="content">
      <h3>{{ title }}</h3>
      <p class="value">{{ value }}</p>
      <p class="change" :class="{ positive: change > 0, negative: change < 0 }">
        {{ change > 0 ? '+' : '' }}{{ change }}% vs 上期
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatsCard',
  props: {
    title: {
      type: String,
      required: true
    },
    value: {
      type: [String, Number],
      required: true
    },
    change: {
      type: Number,
      default: 0
    },
    iconClass: {
      type: String,
      default: 'fas fa-chart-line'
    }
  }
}
</script>

<style scoped>
.stats-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.icon {
  margin-right: 16px;
  font-size: 2em;
  color: #007bff;
}

.content h3 {
  margin: 0 0 8px 0;
  font-size: 0.9em;
  color: #666;
}

.value {
  font-size: 2em;
  font-weight: bold;
  margin: 0 0 4px 0;
}

.change {
  font-size: 0.8em;
  margin: 0;
}

.positive {
  color: #28a745;
}

.negative {
  color: #dc3545;
}
</style>