<template>
  <div class="forum-post">
    <PostListCard
      :post="post"
      @like="handleLike"
      @comment="handleComment"
    />
    <CollapsibleDiscussionPanel
      v-if="showDiscussion"
      :comments="comments"
      :currentUser="currentUser"
      @addComment="handleAddComment"
      @reply="handleReply"
    />
  </div>
</template>

<script>
import PostListCard from './PostListCard.vue'
import CollapsibleDiscussionPanel from './CollapsibleDiscussionPanel.vue'

export default {
  name: 'ForumPost',
  components: {
    PostListCard,
    CollapsibleDiscussionPanel
  },
  props: {
    post: {
      type: Object,
      required: true
    },
    comments: {
      type: Array,
      default: () => []
    },
    currentUser: {
      type: Object,
      required: true
    },
    showDiscussion: {
      type: Boolean,
      default: true
    }
  },
  methods: {
    handleLike(postId) {
      this.$emit('like', postId)
    },
    handleComment(postId) {
      this.$emit('comment', postId)
    },
    handleAddComment(comment) {
      this.$emit('addComment', comment)
    },
    handleReply(commentId, reply) {
      this.$emit('reply', commentId, reply)
    }
  }
}
</script>

<style scoped>
.forum-post {
  margin-bottom: 20px;
}
</style>