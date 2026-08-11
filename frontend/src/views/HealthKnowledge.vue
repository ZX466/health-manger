<template>
  <div class="health-knowledge">

    <div class="content">
      <div class="section-header">
        <h1>📚 健康知识与食谱</h1>
        <p>探索健康知识，发现美味食谱</p>
        <div class="mascot-companion mascot-cat-companion">
          <CharacterAvatar type="hajimi" :animated="true" style="width:50px;height:50px" />
        </div>
      </div>

      <div class="tabs">
        <button :class="{ active: activeTab === 'knowledge' }" @click="activeTab = 'knowledge'">
          📖 健康知识
        </button>
        <button :class="{ active: activeTab === 'recipes' }" @click="activeTab = 'recipes'">
          👨‍🍳 食谱大全
        </button>
        <button :class="{ active: activeTab === 'my-favorites' }" @click="activeTab = 'my-favorites'">
          ⭐ 我的收藏
        </button>
      </div>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <input
          type="text"
          v-model="searchKeyword"
          :placeholder="activeTab === 'knowledge' ? '搜索健康知识...' : '搜索食谱...'"
          @input="handleSearch"
          class="search-input"
        />
        <select v-model="categoryFilter" @change="loadData" class="category-select">
          <option value="">全部分类</option>
          <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
        </select>
      </div>

      <!-- 健康知识列表 -->
      <div v-if="activeTab === 'knowledge'" class="content-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="knowledgeList.length === 0" class="no-data">
          <span class="no-data-icon">📚</span>
          <p>暂无健康知识内容</p>
          <div class="mascot-no-data">
            <MiniCat size="large" animation="wobble" />
            <MiniNailong size="large" />
          </div>
        </div>
        <div v-else class="card-grid">
          <div v-for="item in knowledgeList" :key="item.id" class="knowledge-card" @click="viewKnowledge(item)">
            <div class="card-image" v-if="item.cover_image">
              <img :src="item.cover_image" :alt="item.title" />
              <span class="card-category">{{ item.category_name }}</span>
            </div>
            <div class="card-content">
              <h3>{{ item.title }}</h3>
              <p class="card-summary">{{ item.summary }}</p>
              <div class="card-meta">
                <span class="meta-item">👁️ {{ item.view_count || 0 }}</span>
                <span class="meta-item">👍 {{ item.like_count || 0 }}</span>
                <span class="meta-item">💬 {{ item.comment_count || 0 }}</span>
              </div>
              <div class="card-actions">
                <button @click.stop="toggleLike(item, 'knowledge')" :class="{ liked: item.is_liked }" class="action-btn">
                  {{ item.is_liked ? '❤️' : '🤍' }} {{ item.like_count || 0 }}
                </button>
                <button @click.stop="toggleFavorite(item, 'knowledge')" :class="{ favorited: item.is_favorited }" class="action-btn">
                  {{ item.is_favorited ? '⭐' : '☆' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 食谱列表 -->
      <div v-if="activeTab === 'recipes'" class="content-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="recipeList.length === 0" class="no-data">
          <span class="no-data-icon">👨‍🍳</span>
          <p>暂无食谱内容</p>
          <div class="mascot-no-data">
            <MiniNailong size="large" />
            <MiniCat size="large" animation="wobble" />
          </div>
        </div>
        <div v-else class="card-grid recipe-grid">
          <div v-for="recipe in recipeList" :key="recipe.id" class="recipe-card" @click="viewRecipe(recipe)">
            <div class="recipe-image" v-if="recipe.image">
              <img :src="recipe.image" :alt="recipe.name" />
              <div class="recipe-badge" v-if="recipe.difficulty">
                难度：{{ recipe.difficulty }}
              </div>
            </div>
            <div class="recipe-content">
              <h3>{{ recipe.name }}</h3>
              <p class="recipe-desc">{{ recipe.description }}</p>
              <div class="recipe-info">
                <span>⏱️ {{ recipe.cook_time || '30分钟' }}</span>
                <span>🔥 {{ recipe.calories || '200 kcal' }}</span>
                <span>👥 {{ recipe.servings || '2人份' }}</span>
              </div>
              <div class="recipe-tags" v-if="recipe.tags && recipe.tags.length">
                <span v-for="tag in recipe.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
              </div>
              <div class="card-actions">
                <button @click.stop="toggleLike(recipe, 'recipe')" :class="{ liked: recipe.is_liked }" class="action-btn">
                  {{ recipe.is_liked ? '❤️' : '🤍' }} {{ recipe.like_count || 0 }}
                </button>
                <button @click.stop="toggleFavorite(recipe, 'recipe')" :class="{ favorited: recipe.is_favorited }" class="action-btn">
                  {{ recipe.is_favorited ? '⭐' : '☆' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 我的收藏 -->
      <div v-if="activeTab === 'my-favorites'" class="content-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="favoriteList.length === 0" class="no-data">
          <span class="no-data-icon">⭐</span>
          <p>还没有收藏任何内容</p>
          <div class="mascot-no-data">
            <MiniCat size="large" animation="wobble" />
            <MiniNailong size="large" />
          </div>
          <button @click="activeTab = 'knowledge'" class="browse-btn">去浏览</button>
        </div>
        <div v-else class="card-grid">
          <div v-for="item in favoriteList" :key="`${item.type}-${item.id}`" class="knowledge-card" @click="viewItem(item)">
            <div class="card-image" v-if="item.cover_image || item.image">
              <img :src="item.cover_image || item.image" :alt="item.title || item.name" />
              <span class="card-type-badge">{{ item.type === 'knowledge' ? '知识' : '食谱' }}</span>
            </div>
            <div class="card-content">
              <h3>{{ item.title || item.name }}</h3>
              <p class="card-summary">{{ item.summary || item.description }}</p>
              <div class="card-actions">
                <button @click.stop="removeFavorite(item)" class="action-btn remove-btn">
                  取消收藏
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 趣图推荐 -->
      <div class="meme-section" v-if="activeTab === 'knowledge' || activeTab === 'recipes'">
        <MemeGallery source="gifs" title="奶龙趣图" :count="3" :cols="3" />
      </div>

      <!-- 猜你喜欢（推荐） -->
      <div v-if="(activeTab === 'knowledge' || activeTab === 'recipes') && recommendations.length > 0" class="recommendations">
        <h3>💡 猜你喜欢</h3>
        <div class="rec-list">
          <div v-for="rec in recommendations" :key="'rec-' + rec.id" class="rec-item" @click="viewRecommendation(rec)">
            <span class="rec-title">{{ rec.title || rec.name }}</span>
            <span class="rec-reason">{{ rec.reason }}</span>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pagination">
        <button @click="changePage(currentPage - 1)" :disabled="currentPage <= 1">上一页</button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages">下一页</button>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="showDetail" class="modal-overlay" @click="showDetail = false">
      <div class="detail-modal" @click.stop>
        <div class="modal-header">
          <h2>{{ detailData.title || detailData.name }}</h2>
          <button @click="showDetail = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="detailData.content" class="detail-content" v-html="detailData.content"></div>
          <div v-if="detailData.ingredients" class="ingredients-section">
            <h3>食材清单</h3>
            <ul>
              <li v-for="(ing, idx) in detailData.ingredients" :key="idx">{{ ing }}</li>
            </ul>
          </div>
          <div v-if="detailData.steps" class="steps-section">
            <h3>制作步骤</h3>
            <ol>
              <li v-for="(step, idx) in detailData.steps" :key="idx">{{ step }}</li>
            </ol>
          </div>
        </div>
        <div class="modal-footer">
          <div class="interaction-bar">
            <button @click="toggleLike(detailData, currentDetailType)" :class="{ liked: detailData.is_liked }">
              {{ detailData.is_liked ? '❤️ 已赞' : '🤍 点赞' }}
            </button>
            <button @click="toggleFavorite(detailData, currentDetailType)" :class="{ favorited: detailData.is_favorited }">
              {{ detailData.is_favorited ? '⭐ 已收藏' : '☆ 收藏' }}
            </button>
          </div>
          <div class="comment-section">
            <h4>评论 ({{ comments.length }})</h4>
            <div class="comment-input">
              <textarea v-model="newComment" placeholder="写下你的评论..." rows="2"></textarea>
              <button @click="submitComment" :disabled="!newComment.trim()">发表评论</button>
            </div>
            <div class="comment-list">
              <div v-for="comment in comments" :key="comment.id" class="comment-item">
                <strong>{{ comment.user_name }}</strong>
                <p>{{ comment.content }}</p>
                <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import CharacterAvatar from '../components/CharacterAvatar.vue'
import MemeGallery from '../components/MemeGallery.vue'
import MiniCat from '../components/mascots/MiniCat.vue'
import MiniNailong from '../components/mascots/MiniNailong.vue'

export default {
  name: 'HealthKnowledge',
  components: {
    CharacterAvatar,
    MemeGallery,
    MiniCat,
    MiniNailong
  },
  data() {
    return {
      activeTab: 'knowledge',
      searchKeyword: '',
      categoryFilter: '',
      loading: false,
      currentPage: 1,
      pageSize: 12,
      total: 0,

      knowledgeList: [],
      recipeList: [],
      favoriteList: [],
      recommendations: [],

      showDetail: false,
      detailData: {},
      currentDetailType: '',
      comments: [],
      newComment: '',

      categories: [
        { value: 'nutrition', label: '营养知识' },
        { value: 'exercise', label: '运动健身' },
        { value: 'mental', label: '心理健康' },
        { value: 'disease', label: '疾病预防' },
        { value: 'lifestyle', label: '生活作息' },
        { value: 'breakfast', label: '早餐' },
        { value: 'lunch', label: '午餐' },
        { value: 'dinner', label: '晚餐' },
        { value: 'soup', label: '汤品' },
        { value: 'dessert', label: '甜点' }
      ]
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize)
    }
  },
  watch: {
    activeTab() {
      this.currentPage = 1
      this.searchKeyword = ''
      this.categoryFilter = ''
      this.loadData()
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        if (this.activeTab === 'knowledge') {
          await this.loadKnowledge()
        } else if (this.activeTab === 'recipes') {
          await this.loadRecipes()
        } else if (this.activeTab === 'my-favorites') {
          await this.loadFavorites()
        }
      } catch (err) {
        console.error('加载数据失败:', err)
      } finally {
        this.loading = false
      }
    },

    async loadKnowledge() {
      const params = {
        page: this.currentPage,
        page_size: this.pageSize,
        search: this.searchKeyword,
        category: this.categoryFilter
      }
      const response = await api.getKnowledgeList(params)
      this.knowledgeList = response.data.items || []
      this.total = response.data.total || 0
      this.recommendations = response.data.recommendations || []
    },

    async loadRecipes() {
      const params = {
        page: this.currentPage,
        page_size: this.pageSize,
        search: this.searchKeyword,
        category: this.categoryFilter
      }
      const response = await api.getRecipeList(params)
      this.recipeList = response.data.items || []
      this.total = response.data.total || 0
      this.recommendations = response.data.recommendations || []
    },

    async loadFavorites() {
      const params = {
        page: this.currentPage,
        page_size: this.pageSize
      }
      const response = await api.getFavorites(params)
      this.favoriteList = response.data.items || []
      this.total = response.data.total || 0
    },

    handleSearch() {
      this.currentPage = 1
      this.loadData()
    },

    changePage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
        this.loadData()
      }
    },

    viewKnowledge(item) {
      this.detailData = { ...item }
      this.currentDetailType = 'knowledge'
      this.showDetail = true
      this.loadComments('knowledge', item.id)
    },

    viewRecipe(recipe) {
      this.detailData = { ...recipe }
      this.currentDetailType = 'recipe'
      this.showDetail = true
      this.loadComments('recipe', recipe.id)
    },

    viewItem(item) {
      if (item.type === 'knowledge') {
        this.viewKnowledge(item)
      } else {
        this.viewRecipe(item)
      }
    },

    viewRecommendation(rec) {
      if (rec.type === 'knowledge' || rec.category_type === 'knowledge') {
        this.viewKnowledge(rec)
      } else {
        this.viewRecipe(rec)
      }
    },

    async toggleLike(item, type) {
      try {
        const endpoint = type === 'knowledge' ? 'knowledge' : 'recipe'
        if (item.is_liked) {
          await api.unlikeItem(endpoint, item.id)
          item.is_liked = false
          item.like_count = Math.max(0, (item.like_count || 1) - 1)
        } else {
          await api.likeItem(endpoint, item.id)
          item.is_liked = true
          item.like_count = (item.like_count || 0) + 1
        }
      } catch (err) {
        console.error('操作失败:', err)
      }
    },

    async toggleFavorite(item, type) {
      try {
        const endpoint = type === 'knowledge' ? 'knowledge' : 'recipe'
        if (item.is_favorited) {
          await api.unfavoriteItem(endpoint, item.id)
          item.is_favorited = false
        } else {
          await api.favoriteItem(endpoint, item.id)
          item.is_favorited = true
        }
      } catch (err) {
        console.error('操作失败:', err)
      }
    },

    async removeFavorite(item) {
      try {
        const endpoint = item.type === 'knowledge' ? 'knowledge' : 'recipe'
        await api.unfavoriteItem(endpoint, item.id)
        this.favoriteList = this.favoriteList.filter(f => !(f.id === item.id && f.type === item.type))
        alert('已取消收藏')
      } catch (err) {
        console.error('取消收藏失败:', err)
      }
    },

    async loadComments(type, id) {
      try {
        const endpoint = type === 'knowledge' ? 'knowledge' : 'recipe'
        const response = await api.getComments(endpoint, id)
        this.comments = response.data || []
      } catch (err) {
        this.comments = []
      }
    },

    async submitComment() {
      if (!this.newComment.trim()) return
      try {
        const endpoint = this.currentDetailType === 'knowledge' ? 'knowledge' : 'recipe'
        await api.addComment(endpoint, this.detailData.id, { content: this.newComment })
        this.comments.unshift({
          id: Date.now(),
          user_name: '我',
          content: this.newComment,
          created_at: new Date().toISOString()
        })
        this.newComment = ''
      } catch (err) {
        alert('评论失败')
      }
    },

    formatTime(timeStr) {
      return new Date(timeStr).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.health-knowledge {
  min-height: 100vh;
  background: var(--bg);
}
.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.section-header {
  margin-bottom: 24px;
}
.section-header h1 {
  color: var(--fg);
  margin-bottom: 8px;
}
.section-header p {
  color: var(--muted);
}
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.tabs button {
  padding: 12px 24px;
  border: none;
  background: white;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}
.tabs button.active {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: white;
}
.search-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 24px;
}
.search-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #FFE4D6;
  border-radius: var(--radius);
  font-size: 14px;
  transition: border-color 0.3s;
}
.search-input:focus {
  outline: none;
  border-color: var(--accent);
}
.category-select {
  padding: 12px 16px;
  border: 2px solid #FFE4D6;
  border-radius: var(--radius);
  background: white;
  cursor: pointer;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.knowledge-card, .recipe-card {
  background: white;
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}
.knowledge-card:hover, .recipe-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
}
.card-image, .recipe-image {
  position: relative;
  height: 180px;
  overflow: hidden;
}
.card-image img, .recipe-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.card-category, .card-type-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(255, 155, 113, 0.9);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
}
.recipe-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(245, 101, 101, 0.9);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
}
.card-content, .recipe-content {
  padding: 18px;
}
.card-content h3, .recipe-content h3 {
  color: var(--fg);
  margin-bottom: 8px;
  font-size: 16px;
}
.card-summary, .recipe-desc {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-meta, .recipe-info {
  display: flex;
  gap: 15px;
  color: var(--muted);
  font-size: 13px;
  margin-bottom: 12px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.recipe-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.tag {
  background: #FFF0E8;
  color: var(--accent);
  padding: 3px 10px;
  border-radius: var(--radius);
  font-size: 11px;
}
.card-actions {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}
.action-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid #FFE4D6;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}
.action-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.action-btn.liked, .action-btn.favorited {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: white;
  border-color: transparent;
}
.remove-btn {
  color: var(--danger) !important;
  border-color: var(--danger) !important;
}
.no-data {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: var(--radius);
}
.no-data-icon {
  font-size: 60px;
  display: block;
  margin-bottom: 16px;
}
.browse-btn {
  margin-top: 16px;
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}
.recommendations {
  margin-top: 40px;
  background: white;
  padding: 24px;
  border-radius: var(--radius);
}
.recommendations h3 {
  color: var(--fg);
  margin-bottom: 16px;
}
.rec-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rec-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #FFF8F5;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.3s;
}
.rec-item:hover {
  background: #e8ecf4;
}
.rec-title {
  color: var(--fg);
  font-weight: 500;
}
.rec-reason {
  color: var(--muted);
  font-size: 13px;
}
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
}
.pagination button {
  padding: 10px 20px;
  border: 1px solid #FFE4D6;
  background: white;
  border-radius: var(--radius);
  cursor: pointer;
}
.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  overflow-y: auto;
  padding: 20px;
}
.detail-modal {
  background: white;
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #eee;
}
.modal-header h2 {
  color: var(--fg);
}
.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--muted);
}
.modal-body {
  padding: 24px;
}
.detail-content {
  line-height: 1.8;
  color: var(--fg);
  margin-bottom: 24px;
}
.ingredients-section, .steps-section {
  margin-bottom: 24px;
}
.ingredients-section h3, .steps-section h3 {
  color: var(--accent);
  margin-bottom: 12px;
}
.ingredients-section ul, .steps-section ol {
  padding-left: 20px;
  color: var(--muted);
}
.ingredients-section li, .steps-section li {
  margin-bottom: 8px;
}
.modal-footer {
  padding: 24px;
  border-top: 1px solid #eee;
  background: #FFFCFA;
}
.interaction-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.interaction-bar button {
  padding: 10px 20px;
  border: 1px solid #FFE4D6;
  background: white;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.3s;
}
.interaction-bar button.liked, .interaction-bar button.favorited {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: white;
  border-color: transparent;
}
.comment-section h4 {
  color: var(--fg);
  margin-bottom: 12px;
}
.comment-input {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.comment-input textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #FFE4D6;
  border-radius: var(--radius);
  resize: none;
}
.comment-input button {
  padding: 10px 20px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}
.comment-input button:disabled {
  opacity: 0.5;
}
.comment-list {
  max-height: 300px;
  overflow-y: auto;
}
.comment-item {
  padding: 12px;
  background: white;
  border-radius: var(--radius);
  margin-bottom: 10px;
}
.comment-item strong {
  color: var(--accent);
}
.comment-item p {
  color: var(--muted);
  margin: 6px 0;
}
.comment-time {
  color: var(--muted);
  font-size: 12px;
}
.loading {
  text-align: center;
  padding: 60px;
  color: var(--muted);
}

/* section-header mascot positioning */
.section-header { position: relative; }
.mascot-companion {
  position: absolute; top: 50%; transform: translateY(-50%);
  z-index: 2; pointer-events: none;
}
.mascot-cat-companion { left: 15px; }
.mascot-nailong-companion { right: 15px; }

.mascot-no-data {
  display: flex; align-items: center; justify-content: center;
  gap: 20px; margin: 16px 0; padding: 12px;
}

</style>
