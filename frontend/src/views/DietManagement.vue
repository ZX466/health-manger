<template>
  <div class="diet-management">

    <div class="diet-page">
      <PageHead
        folio="03"
        eyebrow="FOOD / LEDGER"
        title="饮食账本"
        deck="不计算每一口快乐，但至少知道今天的碳水炸弹有多响。"
      >
        <template #actions>
          <button class="btn btn-ghost" type="button" @click="showAddRecord = true">
            <AppIcon name="plus" :size="15" />
            添加记录
          </button>
          <button class="btn btn-primary" type="button" @click="openScan">
            <AppIcon name="camera" :size="15" />
            拍照识餐
          </button>
        </template>
      </PageHead>

      <section class="diet-summary v21-panel" aria-label="今日摄入摘要">
        <div class="panel-head">
          <span class="micro">{{ isToday ? "TODAY'S INTAKE" : 'DAILY INTAKE' }}</span>
          <span class="micro">{{ filterDate }} · {{ foodStats.total_records || 0 }} 条记录</span>
        </div>
        <div class="diet-intake">
          <div>
            <p class="diet-big">{{ foodStats.total_calories || 0 }}<span>kcal</span></p>
            <p class="diet-unit">已摄入 · 目标 2,000 kcal</p>
          </div>
          <div class="diet-left">
            <span class="micro">还能吃</span>
            <strong>{{ remainingCalories }} kcal</strong>
            <p>{{ intakeHint }}</p>
          </div>
        </div>
        <div
          class="diet-progress"
          role="progressbar"
          :aria-valuenow="intakePercent"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <span :style="{ width: intakePercent + '%' }"></span>
        </div>
        <div class="diet-meal-chips">
          <span v-for="(calories, type) in foodStats.meal_type_stats" :key="type" class="meal-chip">
            {{ mealLabel(type) }} <strong>{{ calories }}</strong> kcal
          </span>
          <span v-if="!Object.keys(foodStats.meal_type_stats).length" class="meal-chip is-muted">
            这一天还没有记录
          </span>
        </div>
      </section>

      <div class="diet-toolbar">
        <div class="diet-tabs" role="tablist" aria-label="饮食视图">
          <button
            v-for="tab in dietTabs"
            :key="tab.key"
            type="button"
            role="tab"
            :aria-selected="activeTab === tab.key"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
        <label class="diet-date">
          <span class="sr-only">选择日期</span>
          <input
            type="date"
            v-model="filterDate"
            @change="reloadForDate"
            class="date-picker"
          />
        </label>
      </div>

      <div v-if="activeTab === 'records'" class="diet-grid">
        <section class="diet-panel v21-panel">
          <div class="panel-head">
            <span class="micro">{{ isToday ? "TODAY'S MEALS" : 'MEALS' }}</span>
            <span class="micro">{{ foodRecords.length }} 条</span>
          </div>
          <h2>{{ isToday ? '今天吃了什么' : '这一天吃了什么' }}</h2>

          <div v-if="scanNotice" class="scan-success" role="status">
            <AppIcon name="check" :size="15" />
            {{ scanNotice }}
          </div>

          <div class="diet-records">
            <div v-for="record in foodRecords" :key="record.id" class="diet-record">
              <span class="meal-pill">{{ mealLabel(record.meal_type) }}</span>
              <div class="diet-record-main">
                <strong>{{ record.food_name }}</strong>
                <p>{{ record.quantity_grams }}g · {{ record.calories }} kcal</p>
              </div>
              <button
                class="diet-record-del"
                type="button"
                :aria-label="`删除 ${record.food_name}`"
                @click="deleteRecord(record.id)"
              >
                <AppIcon name="trash" :size="15" />
              </button>
            </div>
            <div v-if="!foodRecords.length" class="diet-empty">
              这一天还没有记录。拍一张，或者手动加一笔。
            </div>
          </div>
        </section>

        <aside class="diet-note v21-panel">
          <div class="panel-head">
            <span class="micro">A SMALL NOTE</span>
            <span class="micro">不是判决书</span>
          </div>
          <h2>今天不用吃得完美</h2>
          <p>捕获“热量刺客”也没关系，快乐是真快乐。晚饭后下楼绕操场走两圈，比在宿舍里自责有用。</p>
          <RouterLink class="text-link" to="/sport-management">
            去记一次散步
            <AppIcon name="arrow" :size="15" />
          </RouterLink>
        </aside>
      </div>

      <section v-if="activeTab === 'foods'" class="diet-panel v21-panel diet-foods-panel">
        <div class="panel-head">
          <span class="micro">FOOD LIBRARY</span>
          <span class="micro">{{ foods.length }} 种食物</span>
        </div>
        <h2>食物库</h2>

        <div class="diet-search">
          <input
            type="text"
            v-model="foodSearch"
            placeholder="搜索食物..."
            aria-label="搜索食物"
            @input="searchFoods"
            class="search-input"
          />
          <button v-if="isAdmin" @click="showAddFood = true" class="btn btn-ghost" type="button">
            <AppIcon name="plus" :size="15" />
            添加食物
          </button>
        </div>

        <div class="diet-foods">
          <article v-for="food in foods" :key="food.id" class="food-tile">
            <div class="food-tile-head">
              <h3>{{ food.name }}</h3>
              <span class="food-cat">{{ food.category || '未分类' }}</span>
            </div>
            <div class="food-facts">
              <span><strong>{{ food.calories_per_100g || 0 }}</strong> kcal</span>
              <span><strong>{{ food.protein_per_100g || 0 }}</strong>g 蛋白质</span>
              <span><strong>{{ food.carbs_per_100g || 0 }}</strong>g 碳水</span>
            </div>
            <button @click="selectFood(food)" class="food-add" type="button">
              添加到记录
              <AppIcon name="arrow" :size="14" />
            </button>
          </article>
        </div>
      </section>

      <div v-if="activeTab === 'stats'" class="diet-stats-grid">
        <section class="diet-panel v21-panel">
          <div class="panel-head">
            <span class="micro">SUMMARY</span>
            <span class="micro">{{ filterDate }}</span>
          </div>
          <h2>这一天吃进去多少</h2>

          <div class="diet-kpis">
            <div>
              <span class="micro">总摄入</span>
              <strong>{{ foodStats.total_calories || 0 }}<em>kcal</em></strong>
            </div>
            <div>
              <span class="micro">记录总数</span>
              <strong>{{ foodStats.total_records || 0 }}<em>条</em></strong>
            </div>
          </div>

          <h3 class="diet-subhead">各餐次热量分布</h3>
          <div v-for="(calories, mealType) in foodStats.meal_type_stats" :key="mealType" class="meal-stat">
            <span class="meal-stat-label">{{ mealLabel(mealType) }}</span>
            <div class="diet-bar">
              <span :style="{ width: getPercentage(calories) + '%' }"></span>
            </div>
            <span class="meal-stat-value">{{ calories }} kcal</span>
          </div>
          <div v-if="!Object.keys(foodStats.meal_type_stats).length" class="diet-empty">
            这一天还没有记录，统计暂时是空的。
          </div>
        </section>

        <aside class="diet-note v21-panel">
          <div class="panel-head">
            <span class="micro">HOW TO READ</span>
            <span class="micro">参考，不是考核</span>
          </div>
          <h2>数字只是参考</h2>
          <p>2,000 kcal 是一个粗略的默认值，实际需求会随体重、活动量和当天状态变化。看趋势，比盯单日数字更有用。</p>
          <RouterLink class="text-link" to="/health-analysis">
            去看健康趋势
            <AppIcon name="arrow" :size="15" />
          </RouterLink>
        </aside>
      </div>
    </div>

    <div v-if="showScan" class="modal-overlay" @click="closeScan">
      <div class="modal scan-modal" @click.stop>
        <div class="scan-head">
          <div>
            <h2>拍照识餐</h2>
            <p class="scan-sub">拍一张，AI 先给草稿；克数和热量都能改，确认后才入库。</p>
          </div>
          <button class="icon-close" type="button" aria-label="关闭拍照识餐" @click="closeScan">
            <AppIcon name="close" :size="17" />
          </button>
        </div>

        <input
          ref="scanInput"
          type="file"
          accept="image/*"
          capture="environment"
          class="sr-only"
          @change="onScanFile"
        />

        <button v-if="!scanPreview" class="scan-drop" type="button" @click="pickScanFile">
          <AppIcon name="camera" :size="24" />
          <strong>拍一张或从相册选</strong>
          <span>支持 JPG / PNG，图片只用于这一次识别</span>
        </button>

        <div v-else class="scan-preview-wrap">
          <img :src="scanPreview" alt="待识别的餐食照片" class="scan-preview" />
          <button class="btn-camera" type="button" @click="pickScanFile">重拍 / 换一张</button>
        </div>

        <div v-if="scanLoading" class="scan-loading" role="status">
          <span class="spinner" aria-hidden="true"></span>
          正在辨认这盘菜，顺便估算一下热量…
        </div>

        <p v-if="scanError" class="scan-error" role="alert">{{ scanError }}</p>

        <template v-if="scanItems.length">
          <div class="scan-meal">
            <label for="scan-meal-type">这是哪一餐</label>
            <select id="scan-meal-type" v-model="scanMealType">
              <option value="breakfast">早餐</option>
              <option value="lunch">午餐</option>
              <option value="dinner">晚餐</option>
              <option value="snack">加餐</option>
            </select>
            <span class="scan-total">合计 {{ scanTotal }} kcal</span>
          </div>

          <div class="scan-list">
            <div v-for="(item, index) in scanItems" :key="index" class="scan-item">
              <div class="scan-item-head">
                <input v-model="item.name" class="scan-name" type="text" maxlength="50" aria-label="食物名称" />
                <span class="scan-confidence">置信度 {{ Math.round((item.confidence || 0) * 100) }}%</span>
                <button class="scan-remove" type="button" @click="scanItems.splice(index, 1)">移除</button>
              </div>
              <div class="scan-fields">
                <label>
                  克数
                  <input v-model.number="item.grams" type="number" min="0" max="5000" step="1" />
                </label>
                <label>
                  热量 kcal
                  <input v-model.number="item.calories" type="number" min="0" max="100000" step="1" />
                </label>
              </div>
            </div>
          </div>

          <p class="scan-note">识别只是估算，确认前请按实际分量改一改。</p>
        </template>

        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="closeScan">取消</button>
          <button
            type="button"
            class="btn-submit"
            :disabled="scanSaving || scanLoading || !scanItems.length"
            @click="confirmScan"
          >
            {{ scanSaving ? '保存中…' : '确认并记录' }}
          </button>
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
import AppIcon from '../components/AppIcon.vue'
import PageHead from '../components/PageHead.vue'
import { localDateKey } from '../utils/date'

export default {
  name: 'DietManagement',
  components: {
    AppIcon,
    PageHead
  },
  data() {
    return {
      activeTab: 'records',
      dietTabs: [
        { key: 'records', label: '饮食记录' },
        { key: 'foods', label: '食物库' },
        { key: 'stats', label: '统计分析' }
      ],
      foodRecords: [],
      foods: [],
      foodStats: { total_calories: 0, total_records: 0, meal_type_stats: {} },
      filterDate: localDateKey(),
      foodSearch: '',
      showAddRecord: false,
      showAddFood: false,
      isAdmin: false,
      newRecord: { food_id: '', quantity_grams: '', meal_type: 'lunch' },
      newFood: { name: '', category: '', calories_per_100g: 0, protein_per_100g: 0, carbs_per_100g: 0 },
      showScan: false,
      scanPreview: '',
      scanObjectUrl: '',
      scanLoading: false,
      scanSaving: false,
      scanError: '',
      scanItems: [],
      scanMealType: 'lunch',
      scanNotice: ''
    }
  },
  computed: {
    scanTotal() {
      return Math.round(this.scanItems.reduce((sum, item) => sum + (Number(item.calories) || 0), 0))
    },
    isToday() {
      return this.filterDate === localDateKey()
    },
    remainingCalories() {
      return Math.max(0, 2000 - (Number(this.foodStats.total_calories) || 0))
    },
    intakePercent() {
      return Math.min(100, Math.round(((Number(this.foodStats.total_calories) || 0) / 2000) * 100))
    },
    intakeHint() {
      const total = Number(this.foodStats.total_calories) || 0
      if (!total) return '先记一笔，今天才有账可算。'
      if (total >= 2000) return '已经到了默认目标，按体感决定要不要再加。'
      return '按 2,000 kcal 估算，留一点空间给下一餐。'
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
        const response = await api.getFoods({ search: this.foodSearch || undefined })
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
    mealLabel(type) {
      return { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐' }[type] || type || '未分类'
    },
    async reloadForDate() {
      await Promise.all([this.loadFoodRecords(), this.loadFoodStats()])
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
    openScan() {
      this.resetScan()
      this.showScan = true
    },
    closeScan() {
      if (this.scanSaving) return
      this.showScan = false
      this.resetScan()
    },
    resetScan() {
      if (this.scanObjectUrl) URL.revokeObjectURL(this.scanObjectUrl)
      this.scanPreview = ''
      this.scanObjectUrl = ''
      this.scanLoading = false
      this.scanSaving = false
      this.scanError = ''
      this.scanItems = []
      this.scanMealType = 'lunch'
      if (this.$refs.scanInput) this.$refs.scanInput.value = ''
    },
    pickScanFile() {
      this.$refs.scanInput?.click()
    },
    onScanFile(event) {
      const file = event.target.files?.[0]
      if (!file) return
      if (!file.type.startsWith('image/')) {
        this.scanError = '请选择一张图片'
        return
      }
      if (file.size > 10 * 1024 * 1024) {
        this.scanError = '图片别超过 10MB，压一下再试'
        return
      }
      if (this.scanObjectUrl) URL.revokeObjectURL(this.scanObjectUrl)
      this.scanObjectUrl = URL.createObjectURL(file)
      this.scanPreview = this.scanObjectUrl
      this.runRecognize(file)
    },
    async runRecognize(file) {
      this.scanLoading = true
      this.scanError = ''
      this.scanItems = []
      try {
        const formData = new FormData()
        formData.append('file', file)
        const { data } = await api.recognizeFoodImage(formData)
        const items = Array.isArray(data?.items) ? data.items : []
        if (!items.length) {
          this.scanError = '这张图没认出食物，换一张更清楚的试试'
          return
        }
        this.scanItems = items.map(item => ({
          name: item.name || '未命名食物',
          grams: Number(item.grams) || 100,
          calories: Number(item.calories) || 0,
          protein: item.protein ?? null,
          fat: item.fat ?? null,
          carbs: item.carbs ?? null,
          confidence: Number(item.confidence) || 0
        }))
      } catch (err) {
        this.scanError = '识别失败：' + this.errMsg(err)
      } finally {
        this.scanLoading = false
      }
    },
    async confirmScan() {
      const items = this.scanItems
        .map(item => ({
          ...item,
          name: String(item.name || '').trim(),
          grams: Number(item.grams),
          calories: Number(item.calories)
        }))
        .filter(item => item.name)
      if (!items.length) {
        this.scanError = '至少保留一样食物再确认'
        return
      }
      if (items.some(item => !Number.isFinite(item.grams) || item.grams <= 0)) {
        this.scanError = '每样食物的克数都要大于 0'
        return
      }

      this.scanSaving = true
      this.scanError = ''
      try {
        for (const item of items) {
          const per100 = (Math.max(0, item.calories) / item.grams) * 100
          const { data: food } = await api.createCustomFood({
            name: item.name,
            calories_per_100g: Math.round(per100 * 10) / 10,
            protein_per_100g: item.protein,
            fat_per_100g: item.fat,
            carbs_per_100g: item.carbs
          })
          await api.createFoodRecord({
            food_id: food.id,
            quantity_grams: item.grams,
            meal_type: this.scanMealType
          })
        }
        this.showScan = false
        this.resetScan()
        await Promise.all([this.loadFoodRecords(), this.loadFoodStats()])
        this.scanNotice = `已记下这餐（${items.length} 样），数字可以随时再改`
        setTimeout(() => { this.scanNotice = '' }, 3600)
      } catch (err) {
        this.scanError = '保存失败：' + this.errMsg(err)
      } finally {
        this.scanSaving = false
      }
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
.scan-btn { display: inline-flex; align-items: center; gap: 6px; }
.scan-success { display: flex; align-items: center; gap: 7px; margin-bottom: 14px; padding: 9px 12px; border-radius: var(--radius-sm); background: var(--success-bg, var(--success-soft)); color: var(--success-fg, var(--success)); font-size: 12px; }
.sr-only { position: absolute; width: 1px; height: 1px; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.scan-modal { max-width: 560px; }
.scan-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.scan-head h2 { margin: 0; }
.scan-sub { margin: 4px 0 0; color: var(--muted); font-size: 12px; line-height: 1.6; }
.icon-close { display: grid; place-items: center; width: 36px; height: 36px; border: var(--border-hairline); border-radius: 50%; background: var(--surface); color: var(--muted); cursor: pointer; }
.scan-drop { display: flex; flex-direction: column; align-items: center; gap: 6px; width: 100%; margin-top: 14px; padding: 28px 16px; border: 1px dashed var(--border); border-radius: var(--radius); background: var(--bg); color: var(--muted); cursor: pointer; }
.scan-drop strong { color: var(--fg); font-size: 14px; }
.scan-drop span { font-size: 11px; }
.scan-preview-wrap { position: relative; margin-top: 14px; }
.scan-preview { display: block; width: 100%; max-height: 240px; object-fit: cover; border-radius: var(--radius); border: var(--border-hairline); }
.btn-camera { position: absolute; right: 10px; bottom: 10px; padding: 7px 11px; border: var(--border-hairline); border-radius: 999px; background: var(--surface); color: var(--fg); font-size: 11px; cursor: pointer; }
.scan-loading { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding: 10px 12px; border-radius: var(--radius-sm); background: var(--accent-soft); color: var(--accent-strong); font-size: 12px; }
.scan-error { margin: 12px 0 0; padding: 9px 11px; border-radius: var(--radius-sm); background: var(--danger-soft); color: var(--danger); font-size: 12px; }
.scan-meal { display: flex; align-items: center; gap: 8px; margin-top: 14px; padding-bottom: 10px; border-bottom: var(--border-hairline); }
.scan-meal label { color: var(--muted); font-size: 12px; }
.scan-meal select { min-height: 36px; padding: 0 8px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--fg); font-size: 12px; }
.scan-total { margin-left: auto; color: var(--fg); font-family: var(--font-mono); font-size: 13px; font-weight: 600; }
.scan-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.scan-item { padding: 10px 12px; border: var(--border-hairline); border-radius: var(--radius-sm); background: var(--bg); }
.scan-item-head { display: flex; align-items: center; gap: 8px; }
.scan-name { flex: 1; min-width: 0; min-height: 34px; padding: 0 10px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--fg); font-size: 13px; font-weight: 600; }
.scan-confidence { color: var(--muted); font-size: 10px; white-space: nowrap; }
.scan-remove { padding: 4px 6px; border: 0; background: none; color: var(--danger); font-size: 11px; cursor: pointer; }
.scan-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }
.scan-fields label { display: flex; align-items: center; gap: 6px; color: var(--muted); font-size: 11px; }
.scan-fields input { flex: 1; min-width: 0; min-height: 34px; padding: 0 8px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--fg); font-size: 12px; }
.scan-note { margin: 10px 0 0; color: var(--muted); font-size: 11px; }
.spinner { width: 14px; height: 14px; flex: 0 0 14px; border-radius: 50%; border: 2px solid color-mix(in oklch, var(--accent) 25%, transparent); border-top-color: var(--accent); animation: diet-spin 0.7s linear infinite; }
@keyframes diet-spin { to { transform: rotate(360deg); } }
.date-picker, .search-input {
  padding: 12px;
  border: 1px solid var(--border);
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
  background: var(--warn-soft);
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
  background: var(--warn-soft);
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
  border: 1px solid var(--border);
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
  background: var(--warn-soft);
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
