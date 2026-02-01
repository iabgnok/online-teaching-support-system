<template>
  <div v-if="preview" class="link-preview" @click="openLink">
    <div v-if="loading" class="preview-loading">
      <i class="el-icon-loading"></i> 加载链接预览...
    </div>

    <template v-else>
      <div v-if="preview.image" class="preview-image">
        <img :src="preview.image" :alt="preview.title" />
      </div>

      <div class="preview-content">
        <div class="preview-title">{{ preview.title }}</div>
        <div v-if="preview.description" class="preview-description">
          {{ preview.description }}
        </div>
        <div class="preview-domain">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16.36,14C16.44,13.34 16.5,12.68 16.5,12C16.5,11.32 16.44,10.66 16.36,10H19.74C19.9,10.64 20,11.31 20,12C20,12.69 19.9,13.36 19.74,14M14.59,19.56C15.19,18.45 15.65,17.25 15.97,16H18.92C17.96,17.65 16.43,18.93 14.59,19.56M14.34,14H9.66C9.56,13.34 9.5,12.68 9.5,12C9.5,11.32 9.56,10.65 9.66,10H14.34C14.43,10.65 14.5,11.32 14.5,12C14.5,12.68 14.43,13.34 14.34,14M12,19.96C11.17,18.76 10.5,17.43 10.09,16H13.91C13.5,17.43 12.83,18.76 12,19.96M8,8H5.08C6.03,6.34 7.57,5.06 9.4,4.44C8.8,5.55 8.35,6.75 8,8M5.08,16H8C8.35,17.25 8.8,18.45 9.4,19.56C7.57,18.93 6.03,17.65 5.08,16M4.26,14C4.1,13.36 4,12.69 4,12C4,11.31 4.1,10.64 4.26,10H7.64C7.56,10.66 7.5,11.32 7.5,12C7.5,12.68 7.56,13.34 7.64,14M12,4.03C12.83,5.23 13.5,6.57 13.91,8H10.09C10.5,6.57 11.17,5.23 12,4.03M18.92,8H15.97C15.65,6.75 15.19,5.55 14.59,4.44C16.43,5.07 17.96,6.34 18.92,8M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
          </svg>
          {{ preview.domain }}
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import api from '../api';

export default {
  name: 'LinkPreview',
  props: {
    url: {
      type: String,
      required: true
    },
    autoLoad: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      preview: null,
      loading: false,
      error: null
    };
  },
  mounted() {
    if (this.autoLoad) {
      this.fetchPreview();
    }
  },
  methods: {
    async fetchPreview() {
      if (!this.url || this.loading) return;

      this.loading = true;
      this.error = null;

      try {
        const response = await api.post('/chat/link_preview', {
          url: this.url
        });
        this.preview = response.data;
      } catch (error) {
        console.error('Fetch link preview failed:', error);
        this.error = error.message;
        // 即使失败也显示基本信息
        this.preview = {
          url: this.url,
          title: this.url,
          domain: new URL(this.url).hostname
        };
      } finally {
        this.loading = false;
      }
    },

    openLink() {
      if (this.url) {
        window.open(this.url, '_blank');
      }
    }
  }
};
</script>

<style scoped>
.link-preview {
  margin-top: 8px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  max-width: 400px;
}

.link-preview:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.preview-loading {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.preview-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: #f5f5f5;
}

.preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-content {
  padding: 12px;
}

.preview-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.preview-description {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.preview-domain {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 4px;
}

.preview-domain svg {
  flex-shrink: 0;
}
</style>
