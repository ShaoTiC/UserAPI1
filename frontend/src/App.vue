<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">明</span>
        <span>明聘</span>
      </div>
      <nav class="nav">
        <button :class="{ active: view === 'resumes' || view === 'detail' }" @click="goResumes">
          <span>☷</span>简历库
        </button>
        <button :class="{ active: view === 'bots' }" @click="goBots">
          <span>◉</span>微信聊天机器人
        </button>
        <button><span>▤</span>岗位管理</button>
        <span class="nav-group">更多</span>
        <button><span>▣</span>私域运营</button>
        <button><span>⌁</span>报表管理</button>
        <button><span>◇</span>组织管理</button>
      </nav>
      <div class="account">© 明聘 · Admin</div>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <h1>{{ pageTitle }}</h1>
          <p>{{ pageSubtitle }}</p>
        </div>
        <div class="top-actions">
          <span class="icon-button">▣</span>
          <span class="icon-button">⇧</span>
          <span class="pill">表</span>
          <span class="user">姜文浩 ▾</span>
        </div>
      </header>

      <section v-if="view === 'resumes'" class="panel resume-list-panel">
        <div class="tabs">
          <button
            v-for="tab in statTabs"
            :key="tab.keyName"
            :class="{ active: filters.status === tab.keyName }"
            @click="setStatus(tab.keyName)"
          >
            {{ tab.label }} <span>({{ tab.count }})</span>
          </button>
        </div>

        <div class="quick-filters">
          <input v-model="filters.keyword" placeholder="搜索姓名、手机号、岗位或机器人" @keyup.enter="loadResumes" />
          <select v-model="filters.gender" @change="loadResumes">
            <option value="">性别：不限</option>
            <option value="男">男</option>
            <option value="女">女</option>
          </select>
          <select v-model="ageRange" @change="applyAgeRange">
            <option value="">年龄：不限</option>
            <option value="20-29">20-29岁</option>
            <option value="30-39">30-39岁</option>
            <option value="40-60">40岁以上</option>
          </select>
          <select v-model="filters.education" @change="loadResumes">
            <option value="">学历：不限</option>
            <option>高中</option>
            <option>大专</option>
            <option>本科</option>
          </select>
          <select v-model="filters.communicationStatus" @change="loadResumes">
            <option value="">沟通状态：不限</option>
            <option>未加微信</option>
            <option>已发消息</option>
            <option>已加微信</option>
            <option>新添加微信开聊人</option>
          </select>
          <button class="ghost" @click="resetFilters">清空筛选</button>
          <button class="primary" @click="loadResumes">修改筛选</button>
        </div>

        <div class="batch-row">
          <label><input type="checkbox" /> 全部选中</label>
          <label><input type="checkbox" /> 取消选中</label>
          <button>批量收藏</button>
          <button>批量移动</button>
          <button>批量添加到聊天机器人</button>
          <button class="danger">关闭自动分配</button>
          <button class="warning">编辑任务</button>
        </div>

        <div v-if="loading" class="empty">正在加载简历...</div>
        <div v-else-if="resumes.length === 0" class="empty">暂无匹配简历</div>
        <div v-else class="resume-cards">
          <article v-for="resume in resumes" :key="resume.id" class="resume-card">
            <div class="resume-select"><input type="checkbox" /></div>
            <div class="resume-content" @click="openDetail(resume.id)">
              <div class="card-head">
                <h3>{{ resume.name }}</h3>
                <div class="tag-group">
                  <span class="robot">{{ resume.robotName }}</span>
                  <span :class="['status-dot', resume.candidateStatus === '可面试' ? 'green' : 'orange']"></span>
                  <span>{{ resume.candidateStatus }}</span>
                  <span>▾</span>
                </div>
              </div>
              <p class="resume-line">
                {{ resume.position }} · {{ resume.city }} · {{ resume.currentSalary }} · {{ resume.expectedSalary }}
              </p>
              <div class="resume-actions">
                <span class="channel blue">微</span>
                <span class="channel green">电</span>
                <span class="channel dark">档</span>
              </div>
              <footer>
                <span>导入于 {{ formatDate(resume.importedAt) }}</span>
                <span class="flag">⚑ 转出</span>
              </footer>
            </div>
          </article>
        </div>

        <div class="pagination">
          <span>共 {{ resumePage.total }} 条</span>
          <button :disabled="resumePage.page <= 1" @click="changeResumePage(-1)">上一页</button>
          <b>{{ resumePage.page }}</b>
          <button :disabled="resumePage.page * resumePage.size >= resumePage.total" @click="changeResumePage(1)">下一页</button>
        </div>
      </section>

      <section v-if="view === 'detail' && selectedResume" class="panel detail-panel">
        <button class="back-button" @click="goResumes">← 返回简历库</button>
        <div class="detail-section">
          <h2>基本信息</h2>
          <div class="detail-grid">
            <InfoItem label="姓名" :value="selectedResume.name" />
            <InfoItem label="性别" :value="selectedResume.gender" />
            <InfoItem label="最高学历" :value="selectedResume.highestEducation" />
            <InfoItem label="年龄" :value="`${selectedResume.age}岁`" />
            <InfoItem label="工作年限" :value="`${selectedResume.workYears}年`" />
            <InfoItem label="户口" value="-" />
            <InfoItem label="微信" :value="selectedResume.phone" />
            <InfoItem label="手机" :value="selectedResume.email || '-'" />
          </div>
        </div>

        <div class="detail-section">
          <h2>薪资/期望</h2>
          <div class="detail-grid four">
            <InfoItem label="目前状态" :value="selectedResume.intention" strong />
            <InfoItem label="期望薪水" :value="selectedResume.expectedSalary" />
            <InfoItem label="目前薪水" :value="selectedResume.currentSalary" />
            <InfoItem label="意向城市" :value="selectedResume.city" strong />
          </div>
        </div>

        <div class="detail-section">
          <h2>自我评价</h2>
          <div class="summary-box">{{ selectedResume.advantages || '暂无内容' }}</div>
        </div>

        <div class="detail-section">
          <h2>教育背景</h2>
          <div class="timeline-card">
            <span>{{ year(selectedResume.educationStart) }} - {{ year(selectedResume.educationEnd) }}</span>
            <div>
              <strong>{{ selectedResume.school }}</strong>
              <p>{{ selectedResume.degree }} · {{ selectedResume.major }}</p>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h2>工作经验</h2>
          <div class="timeline-card work">
            <span>{{ month(selectedResume.workStart) }} - {{ month(selectedResume.workEnd) }}</span>
            <div>
              <strong>{{ selectedResume.company }} · {{ selectedResume.workPosition }}</strong>
              <p>{{ selectedResume.workDescription }}</p>
            </div>
          </div>
        </div>
      </section>

      <section v-if="view === 'bots'" class="panel bots-panel">
        <div class="bot-toolbar">
          <input v-model="botKeyword" placeholder="请输入要搜索的微信聊天机器人名称或微信号" @keyup.enter="loadBots" />
          <button class="primary" @click="loadBots">搜索</button>
          <button class="primary">+ 创建聊天机器人</button>
        </div>
        <div v-if="botLoading" class="empty">正在加载机器人...</div>
        <div v-else class="bot-grid">
          <article v-for="bot in bots" :key="bot.id" class="bot-card">
            <span class="wechat-badge">微</span>
            <button class="more">⋯</button>
            <div class="bot-avatar">{{ bot.name.slice(0, 1) }}</div>
            <div>
              <h3>{{ bot.name }}</h3>
              <p>{{ bot.wechatId }}</p>
              <small>已绑定简历数：{{ bot.boundResumeCount }}</small>
            </div>
            <footer>
              <span :class="['bot-state', bot.status]">{{ bot.status === 'active' ? '在线' : '离线' }}</span>
            </footer>
          </article>
        </div>
        <div class="pagination align-right">
          <span>共{{ botPage.total }}条</span>
          <button :disabled="botPage.page <= 1" @click="changeBotPage(-1)">上一页</button>
          <b>{{ botPage.page }}</b>
          <button :disabled="botPage.page * botPage.size >= botPage.total" @click="changeBotPage(1)">下一页</button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { chatBotApi, resumeApi } from './api'

const InfoItem = defineComponent({
  props: {
    label: String,
    value: [String, Number],
    strong: Boolean,
  },
  setup(props) {
    return () =>
      h('div', { class: 'info-item' }, [
        h('span', props.label),
        h('strong', { class: props.strong ? 'highlight' : '' }, props.value || '-'),
      ])
  },
})

const view = ref('resumes')
const loading = ref(false)
const botLoading = ref(false)
const resumes = ref([])
const selectedResume = ref(null)
const stats = ref([])
const bots = ref([])
const ageRange = ref('')
const botKeyword = ref('')

const filters = reactive({
  keyword: '',
  status: 'all',
  gender: '',
  education: '',
  communicationStatus: '',
  minAge: null,
  maxAge: null,
})

const resumePage = reactive({ page: 1, size: 8, total: 0 })
const botPage = reactive({ page: 1, size: 12, total: 0 })

const defaultTabs = [
  { keyName: 'all', label: '全部', count: 0 },
  { keyName: 'unassigned', label: '未分配', count: 0 },
  { keyName: 'assigned', label: '已分配', count: 0 },
  { keyName: 'boss', label: 'BOSS', count: 0 },
  { keyName: 'phone', label: '手机上传', count: 0 },
  { keyName: 'previous', label: '前程无忧', count: 0 },
]

const statTabs = computed(() => (stats.value.length ? stats.value : defaultTabs))
const pageTitle = computed(() => (view.value === 'bots' ? '微信聊天机器人' : view.value === 'detail' ? '简历' : '简历库'))
const pageSubtitle = computed(() => (view.value === 'detail' ? '查看候选人基础资料、教育背景和工作经历' : ''))

async function loadStats() {
  stats.value = await resumeApi.stats()
}

async function loadResumes() {
  loading.value = true
  try {
    const data = await resumeApi.list({
      ...filters,
      page: resumePage.page,
      size: resumePage.size,
    })
    resumes.value = data.records
    resumePage.total = data.total
  } finally {
    loading.value = false
  }
}

async function openDetail(id) {
  selectedResume.value = await resumeApi.detail(id)
  view.value = 'detail'
}

async function loadBots() {
  botLoading.value = true
  try {
    const data = await chatBotApi.list({
      keyword: botKeyword.value,
      page: botPage.page,
      size: botPage.size,
    })
    bots.value = data.records
    botPage.total = data.total
  } finally {
    botLoading.value = false
  }
}

function setStatus(status) {
  filters.status = status
  resumePage.page = 1
  loadResumes()
}

function applyAgeRange() {
  const [min, max] = ageRange.value ? ageRange.value.split('-').map(Number) : [null, null]
  filters.minAge = min
  filters.maxAge = max
  loadResumes()
}

function resetFilters() {
  Object.assign(filters, {
    keyword: '',
    status: 'all',
    gender: '',
    education: '',
    communicationStatus: '',
    minAge: null,
    maxAge: null,
  })
  ageRange.value = ''
  resumePage.page = 1
  loadResumes()
}

function changeResumePage(offset) {
  resumePage.page += offset
  loadResumes()
}

function changeBotPage(offset) {
  botPage.page += offset
  loadBots()
}

function goResumes() {
  view.value = 'resumes'
  selectedResume.value = null
}

function goBots() {
  view.value = 'bots'
  if (!bots.value.length) {
    loadBots()
  }
}

function formatDate(value) {
  return value ? String(value).slice(0, 10) : '-'
}

function year(value) {
  return value ? String(value).slice(0, 4) : '-'
}

function month(value) {
  return value ? String(value).slice(0, 7) : '-'
}

onMounted(async () => {
  await Promise.all([loadStats(), loadResumes()])
})
</script>
