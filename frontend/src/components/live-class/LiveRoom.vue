<template>
  <div class="live-room">
    <LiveClassToolbar
      :isTeacher="isTeacher"
      :isRecording="isRecording"
      @startRecording="handleStartRecording"
      @stopRecording="handleStopRecording"
      @toggleScreenShare="handleToggleScreenShare"
    />
    <div class="live-content">
      <div class="main-area">
        <WhiteBoard
          :drawingData="drawingData"
          :isTeacher="isTeacher"
          @updateDrawing="handleUpdateDrawing"
        />
        <LiveClassChatPanel
          :discussion-conversation-id="discussionConversationId"
          :class-group-conversation-id="classGroupConversationId"
          :role="userRole"
          :is-online="isOnline"
          :online-count="onlineCount"
          :is-collapsed="chatCollapsed"
          :discussion-unread="discussionUnread"
          :class-group-unread="classGroupUnread"
          :messages="chatMessages"
          @switch-tab="handleSwitchTab"
          @send-message="handleSendMessage"
          @load-more="handleLoadMore"
          @reply="handleReply"
          @edit="handleEdit"
          @delete="handleDelete"
          @open-comments="handleOpenComments"
          @react="handleReact"
          @pin="handlePin"
          @toggle-collapse="handleToggleChatCollapse"
          @start-attendance="handleStartAttendance"
          @publish-task="handlePublishTask"
          @share-board="handleShareBoard"
          @raise-hand="handleRaiseHand"
        />
      </div>
      <ParticipantsPanel
        :participants="participants"
        :currentUser="currentUser"
        @raiseHand="handleRaiseHand"
        @muteParticipant="handleMuteParticipant"
      />
    </div>
    <LiveStatusBanner
      :status="liveStatus"
      :startTime="startTime"
    />
  </div>
</template>

<script>
import LiveClassToolbar from './LiveClassToolbar.vue'
import WhiteBoard from './WhiteBoard.vue'
import LiveClassChatPanel from './LiveClassChatPanel.vue'
import ParticipantsPanel from './ParticipantsPanel.vue'
import LiveStatusBanner from './LiveStatusBanner.vue'

export default {
  name: 'LiveRoom',
  components: {
    LiveClassToolbar,
    WhiteBoard,
    LiveClassChatPanel,
    ParticipantsPanel,
    LiveStatusBanner
  },
  props: {
    isTeacher: {
      type: Boolean,
      default: false
    },
    isRecording: {
      type: Boolean,
      default: false
    },
    drawingData: {
      type: Array,
      default: () => []
    },
    chatMessages: {
      type: Array,
      default: () => []
    },
    participants: {
      type: Array,
      default: () => []
    },
    currentUser: {
      type: Object,
      required: true
    },
    liveStatus: {
      type: String,
      default: 'live'
    },
    startTime: {
      type: String,
      default: ''
    },
    // 新增的聊天相关props
    discussionConversationId: {
      type: [String, Number],
      default: null
    },
    classGroupConversationId: {
      type: [String, Number],
      default: null
    },
    userRole: {
      type: String,
      default: 'student'
    },
    isOnline: {
      type: Boolean,
      default: true
    },
    onlineCount: {
      type: Number,
      default: 0
    },
    chatCollapsed: {
      type: Boolean,
      default: false
    },
    discussionUnread: {
      type: Number,
      default: 0
    },
    classGroupUnread: {
      type: Number,
      default: 0
    }
  },
  emits: [
    'startRecording',
    'stopRecording',
    'toggleScreenShare',
    'updateDrawing',
    'sendMessage',
    'raiseHand',
    'muteParticipant',
    'switchTab',
    'loadMore',
    'reply',
    'edit',
    'delete',
    'openComments',
    'react',
    'pin',
    'toggleChatCollapse',
    'startAttendance',
    'publishTask',
    'shareBoard'
  ],
  methods: {
    handleStartRecording() {
      this.$emit('startRecording')
    },
    handleStopRecording() {
      this.$emit('stopRecording')
    },
    handleToggleScreenShare() {
      this.$emit('toggleScreenShare')
    },
    handleUpdateDrawing(data) {
      this.$emit('updateDrawing', data)
    },
    handleSendMessage(message) {
      this.$emit('sendMessage', message)
    },
    handleRaiseHand() {
      this.$emit('raiseHand')
    },
    handleMuteParticipant(participantId) {
      this.$emit('muteParticipant', participantId)
    },
    // 新增的聊天相关方法
    handleSwitchTab(tab) {
      this.$emit('switchTab', tab)
    },
    handleLoadMore(tab) {
      this.$emit('loadMore', tab)
    },
    handleReply(data) {
      this.$emit('reply', data)
    },
    handleEdit(data) {
      this.$emit('edit', data)
    },
    handleDelete(data) {
      this.$emit('delete', data)
    },
    handleOpenComments(data) {
      this.$emit('openComments', data)
    },
    handleReact(data) {
      this.$emit('react', data)
    },
    handlePin(data) {
      this.$emit('pin', data)
    },
    handleToggleChatCollapse() {
      this.$emit('toggleChatCollapse')
    },
    handleStartAttendance() {
      this.$emit('startAttendance')
    },
    handlePublishTask() {
      this.$emit('publishTask')
    },
    handleShareBoard() {
      this.$emit('shareBoard')
    }
  }
}
</script>

<style scoped>
.live-room {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.live-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>