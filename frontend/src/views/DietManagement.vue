<template>
  <div class="diet-management">

    <div class="content">
      <div class="section-header">
        <h1> 饮食管理</h1>
        <p>记录每日饮食，管理营养摄入</p>
        <div class="mascot-companion mascot-cat-companion">
          <MiniCat />
        </div>
      </div>

      <div class="tabs">
        <button :class="{ active: activeTab === 'records' }" @click="activeTab = 'records'">
           饮食记录
        </button>
        <button :class="{ active: activeTab === 'foods' }" @click="activeTab = 'foods'">
           食物库
        </button>
        <button :class="{ active: activeTab === 'stats' }" @click="activeTab = 'stats'">
           统计分析
        </button>
      </div>

      <div v-if="activeTab === 'records'" class="tab-content">
        <div class="action-bar">
          <button @click="showAddRecord = true" class="btn-primary">
             添加饮食记录
          </button>
          <input 
            type="date" 
            v-model="filterDate" 
            @change="loadFoodRecords"
            class="date-picker"
          />
        </div>

        <div class="records-list">
          <div v-for="record in foodRecords" :key="record.id" class="record-card">
            <div class="record-info">
              <div class="food-name">{{ record.food_name }}</div>
              <div class="record-meta">
                <span> {{ record.meal_type || '未分类' }}</span>
                <span> {{ record.quantity_grams }}g</span>
                <span> {{ record.calories }} kcal</span>
                <span> {{ formatDate(record.record_date) }}</span>
              </div>
            </div>
            <button @click="deleteRecord(record.id)" class="btn-delete">删除</button>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'foods'" class="tab-content">
        <div class="action-bar">
          <button v-if="isAdmin" @click="showAddFood = true" class="btn-primary">
             添加食物
          </button>
          <input 
            type="text" 
            v-model="foodSearch" 
            placeholder="搜索食物..."
            @input="searchFoods"
            class="search-input"
          />
        </div>

        <div class="foods-grid">
          <div v-for="food in foods" :key="food.id" class="food-card">
            <h3>{{ food.name }}</h3>
            <p class="food-category">{{ food.category || '未分类' }}</p>
            <div class="food-nutrition">
              <span> {{ food.calories_per_100g || 0 }} kcal</span>
              <span> {{ food.protein_per_100g || 0 }}g 蛋白质</span>
              <span> {{ food.carbs_per_100g || 0 }}g 碳水</span>
            </div>
            <button @click="selectFood(food)" class="btn-small">添加到记录</button>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'stats'" class="tab-content">
        <div class="stats-cards">
          <div class="stat-card">
            <h3>总摄入热量</h3>
            <div class="stat-value">{{ foodStats.total_calories }} kcal</div>
          </div>
          <div class="stat-card">
            <h3>记录总数</h3>
            <div class="stat-value">{{ foodStats.total_records }}</div>
          </div>
        </div>
        <div class="meal-stats">
          <h3>各餐次热量分布</h3>
          <div v-for="(calories, mealType) in foodStats.meal_type_stats" :key="mealType" class="meal-stat">
            <span>{{ mealType }}</span>
            <div class="progress-bar">
              <div class="progress" :style="{ width: getPercentage(calories) + '%' }"></div>
            </div>
            <span>{{ calories }} kcal</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAddRecord" class="modal-overlay" @click="showAddRecord = false">
      <div class="modal" @click.stop>
        <h2>添加饮食记录</h2>
        <form @submit.prevent="submitFoodRecord">
          <div class="form-group">
            <label>食物</label>
            <select v-model="newRecord.food_id" required>
              <option value="">选择食物</option>
              <option v-for="food in foods" :key="food.id" :value="food.id">
                {{ food.name }} ({{ food.calories_per_100g || 0 }} kcal/100g)
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>摄入量 (克)</label>
            <input type="number" v-model.number="newRecord.quantity_grams" required min="1" />
          </div>
          <div class="form-group">
            <label>餐次类型</label>
            <select v-model="newRecord.meal_type">
              <option value="breakfast">早餐</option>
              <option value="lunch">午餐</option>
              <option value="dinner">晚餐</option>
              <option value="snack">加餐</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddRecord = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-submit">确定</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showAddFood" class="modal-overlay" @click="showAddFood = false">
      <div class="modal" @click.stop>
        <h2>添加食物</h2>
        <form @submit.prevent="submitFood">
          <div class="form-group">
            <label>食物名称</label>
            <input type="text" v-model="newFood.name" required />
          </div>
          <div class="form-group">
            <label>分类</label>
            <select v-model="newFood.category">
              <option value="主食">主食</option>
              <option value="肉类">肉类</option>
              <option value="蔬菜">蔬菜</option>
              <option value="水果">水果</option>
              <option value="奶制品">奶制品</option>
              <option value="零食">零食</option>
            </select>
          </div>
          <div class="form-group">
            <label>热量 (kcal/100g)</label>
            <input type="number" v-model.number="newFood.calories_per_100g" step="0.1" />
          </div>
          <div class="form-group">
            <label>蛋白质 (g/100g)</label>
            <input type="number" v-model.number="newFood.protein_per_100g" step="0.1" />
          </div>
          <div class="form-group">
            <label>碳水化合物 (g/100g)</label>
            <input type="number" v-model.number="newFood.carbs_per_100g" step="0.1" />
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddFood = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-submit">确定</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import MiniCat from '../components/mascots/MiniCat.vue'

export default {
  name: 'DietManagement',
  components: {
    MiniCat
  },
  data() {
    return {
      activeTab: 'records',
      foodRecords: [],
      foods: [],
      foodStats: { total_calories: 0, total_records: 0, meal_type_stats: {} },
      filterDate: new Date().toISOString().split('T')[0],
      foodSearch: '',
      showAddRecord: false,
      showAddFood: false,
      isAdmin: false,
      newRecord: { food_id: '', quantity_grams: '', meal_type: 'lunch' },
      newFood: { name: '', category: '', calories_per_100g: 0, protein_per_100g: 0, carbs_per_100g: 0 }
    }
  },
  async mounted() {
    await this.loadCurrentUser()
    await this.loadFoodRecords()
    await this.loadFoods()
    await this.loadFoodStats()
  },
  methods: {
    async loadCurrentUser() {
      try {
        const response = await api.getCurrentUser()
        this.isAdmin = !!response.data?.is_admin
      } catch (err) {
        this.isAdmin = false
      }
    },
    errMsg(err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length) {
        // FastAPI 422 校验错误为数组 [{ loc, msg, type }, ...]
        return detail.map(d => d.msg || String(d)).join('；')
      }
      return err.message || '未知错误'
    },
    async loadFoodRecords() {
      try {
        const response = await api.getFoodRecords({ start_date: this.filterDate, end_date: this.filterDate })
        this.foodRecords = response.data
      } catch (err) {
        console.error('加载饮食记录失败:', err)
      }
    },
    async loadFoods() {
      try {
        const response = await api.getFoods({ search: this.foodSearch })
        this.foods = response.data
      } catch (err) {
        console.error('加载食物库失败:', err)
      }
    },
    async loadFoodStats() {
      try {
        const response = await api.getFoodStats({ start_date: this.filterDate, end_date: this.filterDate })
        this.foodStats = response.data
      } catch (err) {
        console.error('加载统计失败:', err)
      }
    },
    async searchFoods() {
      await this.loadFoods()
    },
    async submitFoodRecord() {
      try {
        await api.createFoodRecord(this.newRecord)
        this.showAddRecord = false
        this.newRecord = { food_id: '', quantity_grams: '', meal_type: 'lunch' }
        await this.loadFoodRecords()
        await this.loadFoodStats()
        alert('添加成功')
      } catch (err) {
        alert('添加失败：' + this.errMsg(err))
      }
    },
    async submitFood() {
      try {
        await api.createFood(this.newFood)
        this.showAddFood = false
        this.newFood = { name: '', category: '', calories_per_100g: 0, protein_per_100g: 0, carbs_per_100g: 0 }
        await this.loadFoods()
        alert('添加成功')
      } catch (err) {
        alert('添加失败：' + this.errMsg(err))
      }
    },
    async deleteRecord(id) {
      if (confirm('确定要删除这条记录吗？')) {
        try {
          await api.deleteFoodRecord(id)
          await this.loadFoodRecords()
          await this.loadFoodStats()
          alert('删除成功')
        } catch (err) {
          alert('删除失败')
        }
      }
    },
    selectFood(food) {
      this.newRecord.food_id = food.id
      this.activeTab = 'records'
      this.showAddRecord = true
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleString('zh-CN')
    },
    getPercentage(calories) {
      const max = Math.max(...Object.values(this.foodStats.meal_type_stats))
      return max > 0 ? (calories / max) * 100 : 0
    }
  }
}
</script>

<style scoped>
.diet-management {
  min-height: 100vh;
  background: var(--bg);
}
.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.section-header {
  margin-bottom: 30px;
}
.section-header h1 {
  color: var(--fg);
  margin-bottom: 10px;
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
  background: var(--accent);
  color: white;
}
.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.btn-primary {
  padding: 12px 24px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 600;
}
.date-picker, .search-input {
  padding: 12px;
  border: 1px solid #FFE4D6;
  border-radius: var(--radius);
  font-size: 14px;
}
.search-input {
  flex: 1;
}
.record-card {
  background: white;
  padding: 20px;
  border-radius: var(--radius);
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.food-name {
  font-size: 18px;
  font-weight: bold;
  color: var(--fg);
  margin-bottom: 8px;
}
.record-meta {
  display: flex;
  gap: 15px;
  color: var(--muted);
  font-size: 14px;
}
.btn-delete {
  padding: 8px 16px;
  background: #fee;
  color: var(--danger);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}
.foods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}
.food-card {
  background: white;
  padding: 20px;
  border-radius: var(--radius);
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.food-card h3 {
  color: var(--fg);
  margin-bottom: 8px;
}
.food-category {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 12px;
}
.food-nutrition {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 15px;
  font-size: 14px;
  color: var(--muted);
}
.btn-small {
  padding: 8px 16px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  width: 100%;
}
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}
.stat-card {
  background: white;
  padding: 24px;
  border-radius: var(--radius);
  text-align: center;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.stat-card h3 {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 10px;
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--accent);
}
.meal-stats {
  background: white;
  padding: 24px;
  border-radius: var(--radius);
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.meal-stat {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}
.progress-bar {
  flex: 1;
  height: 20px;
  background: #FFF0E8;
  border-radius: 10px;
  overflow: hidden;
}
.progress {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: white;
  padding: 30px;
  border-radius: var(--radius);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}
.modal h2 {
  margin-bottom: 20px;
  color: var(--fg);
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--muted);
  font-weight: 500;
}
.form-group input, .form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #FFE4D6;
  border-radius: var(--radius);
  font-size: 14px;
}
.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.btn-cancel {
  padding: 12px 24px;
  background: #FFF0E8;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}
.btn-submit {
  padding: 12px 24px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}

/* section-header mascot positioning */
.section-header { position: relative; }
.mascot-companion {
  position: absolute; top: 50%; transform: translateY(-50%);
  z-index: 2; pointer-events: none;
}
.mascot-cat-companion { left: 15px; }
.mascot-nailong-companion { right: 15px; }

</style>
