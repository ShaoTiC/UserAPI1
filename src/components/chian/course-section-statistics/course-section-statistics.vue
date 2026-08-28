<template>
  <div class="wrapper">
    <h1>课程章节统计</h1>
    <div class="search-bar">
      <span class="search-label">课程ID：</span>
      <Input
        v-model="filter.courseId"
        placeholder="请输入课程ID"
        clearable
        style="width: 220px"
        @on-enter="onSearch"
      />
      <Button type="primary" @click="onSearch">查询</Button>
      <Button @click="resetInput">重置</Button>
    </div>

    <Loading v-if="showLoading"></Loading>

    <i-table
      v-if="!showLoading"
      border
      :columns="columns"
      :data="data"
      stripe
      highlight-row
    ></i-table>

    <div class="pagination-wrap">
      <div class="table-total">
        当前显示{{ pagination.realSize }}条数据，
        总共{{ pagination.total }}条
      </div>

      <Page
        @on-change="changePage"
        :total="pagination.total"
        show-sizer
        @on-page-size-change="changeCurrSize"
        :current="pagination.pageIndex"
        :page-size="pagination.currSize"
      ></Page>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CourseSectionStatistics',
  components: {},
  props: {},
  data() {
    return {
      showLoading: false,
      filter: {
        appId: 'debug',
        token: 'debug',
        requestId: 'debug',
        userId: '',
        subjectId: '',
        sectionId: '',
        sessionId: '',
        courseId: '',
        textBook: '',
        loCode: ''
      },
      pagination: {
        pageIndex: 1,
        total: 0,
        pageSize: 0,
        currSize: 10,
        realSize: 0,
        orderType: 1
      },
      data: [],
      columns: [
        {
          title: '序号',
          width: 70,
          align: 'center',
          render: (h, params) => {
            const index =
              (this.pagination.pageIndex - 1) * this.pagination.currSize +
              params.index +
              1
            return h('span', index)
          }
        },
        {
          title: '课程ID',
          key: 'courseId',
          minWidth: 120,
          align: 'center'
        },
        {
          title: '章节ID',
          key: 'sectionId',
          minWidth: 120,
          align: 'center'
        },
        {
          title: '章节名称',
          key: 'name',
          minWidth: 160,
          render: (h, params) => {
            return h('span', params.row.name || '-')
          }
        },
        {
          title: '知识点数量',
          key: 'loCodeCount',
          width: 110,
          align: 'center'
        },
        {
          title: '知识点 LoCode',
          key: 'loCodes',
          minWidth: 280,
          render: (h, params) => {
            const codes = params.row.loCodes || []
            if (!codes.length) {
              return h('span', '-')
            }
            return h(
              'div',
              codes.map(code => {
                return h(
                  'span',
                  {
                    class: 'lo-code-item'
                  },
                  code
                )
              })
            )
          }
        }
      ]
    }
  },
  created() {},
  mounted() {},
  watch: {},
  computed: {},
  methods: {
    onSearch() {
      this.pagination.pageIndex = 1
      this.getInitData()
    },

    getInitData(d) {
      if (d != null) {
        this.filter.userId = d.userId
        this.filter.subjectId = d.subjectId
        this.filter.sectionId = d.sectionId
        this.filter.sessionId = d.sessionId
        this.filter.loCode = d.loCode
        this.filter.courseId = d.courseId
        this.filter.textBook = d.textBook
      }

      this.queryList()
    },

    queryList() {
      const param = {
        query: this.filter,
        pagination: this.pagination
      }

      this.showLoading = true

      // TODO: 后端接口尚未开发，不要在此处填写虚构 URL。
      // 接口就绪后：在 index.js 中补充 axios + queryList，再改为：
      // queryList(param).then(res => { ... })
      this.bindMockTable(param)
    },

    // TODO: MOCK DATA，仅用于验证页面结构，后端接口就绪后删除
    bindMockTable(param) {
      const list = this.buildMockStatList(param.query)
      const pageIndex = param.pagination.pageIndex || 1
      const pageSize = param.pagination.currSize || 10
      const start = (pageIndex - 1) * pageSize
      const pageData = list.slice(start, start + pageSize)

      this.data = pageData
      this.pagination.total = list.length
      this.pagination.realSize = pageData.length
      this.showLoading = false
    },

    // TODO: MOCK DATA，字段取自 ALE_SECTION / ALE_SEGMENT 截图，最终以后端 VO 为准
    buildMockStatList(query) {
      const sectionList = this.getMockSectionList()
      const segmentList = this.getMockSegmentList()
      const courseId = query && query.courseId ? String(query.courseId).trim() : ''

      let sections = sectionList.filter(item => item.sectionType === 'CHAPTER')
      if (courseId) {
        sections = sections.filter(item => String(item.courseId) === courseId)
      }

      return sections.map(section => {
        const segments = segmentList.filter(item => {
          return String(item.sectionId) === String(section.sectionId)
        })
        const loCodes = []
        segments.forEach(item => {
          if (item.loCode && loCodes.indexOf(item.loCode) === -1) {
            loCodes.push(item.loCode)
          }
        })
        return {
          courseId: section.courseId,
          sectionId: section.sectionId,
          name: section.name,
          loCodeCount: loCodes.length,
          loCodes: loCodes
        }
      })
    },

    // TODO: MOCK DATA，模拟 ALE_SECTION（章节表）
    // 截图可见字段：courseId, name, textbook, released, sectionType,
    // stageCode, chapterLabel, ruleGroupId, seq / sequences, pkeyMapping
    // 截图未直接展示 sectionId 列，mock 中暂用 sectionId 与 ALE_SEGMENT 关联，
    // 真实关联字段需等后端 Entity / VO 确认（可能是 _id 或 pkeyMapping）
    getMockSectionList() {
      return [
        {
          courseId: '10000061',
          sectionId: 10000074,
          name: '第八章：压强',
          textbook: '27',
          released: 300,
          sectionType: 'CHAPTER',
          stageCode: 30,
          chapterLabel: 8,
          ruleGroupId: 40101
        },
        {
          courseId: '10000061',
          sectionId: 10000081,
          name: '测试章',
          textbook: '27',
          released: 100,
          sectionType: 'CHAPTER',
          stageCode: 30,
          chapterLabel: 1,
          ruleGroupId: 40101
        },
        {
          courseId: '10000061',
          sectionId: 10000083,
          name: '第九章：浮力',
          textbook: '27',
          released: 200,
          sectionType: 'CHAPTER',
          stageCode: 30,
          chapterLabel: 9,
          ruleGroupId: 40103
        },
        {
          courseId: '10000061',
          sectionId: 10000086,
          name: '期中冲刺',
          textbook: '27',
          released: 100,
          sectionType: 'CHAPTER',
          stageCode: 30,
          chapterLabel: 5,
          ruleGroupId: 20103
        },
        {
          courseId: '10000061',
          sectionId: 10000089,
          name: '第一章',
          textbook: '27',
          released: 300,
          sectionType: 'CHAPTER',
          stageCode: 30,
          chapterLabel: 1,
          ruleGroupId: 40101
        },
        {
          courseId: '10000061',
          sectionId: 10000061,
          name: '课程根节点',
          textbook: '27',
          released: 500,
          sectionType: 'COURSE',
          stageCode: 30,
          chapterLabel: 0,
          ruleGroupId: 0
        },
        {
          courseId: '10000139',
          sectionId: 10000140,
          name: '因数与倍数-冲刺章',
          textbook: '22',
          released: 300,
          sectionType: 'CHAPTER',
          stageCode: 40,
          chapterLabel: 3,
          ruleGroupId: 20103
        }
      ]
    },

    // TODO: MOCK DATA，模拟 ALE_SEGMENT（课次表）
    // 截图可见字段：_id, snapshotId, utime, storageStatus, sectionId,
    // classId, courseId, tags, loCode, traceId, pkeyMapping
    getMockSegmentList() {
      return [
        {
          sectionId: 10000074,
          classId: 10000075,
          courseId: 10000061,
          loCode: 'wl_lx_gg_s004',
          storageStatus: 'USEING'
        },
        {
          sectionId: 10000074,
          classId: 10000076,
          courseId: 10000061,
          loCode: 'wl_lx_gg_s015',
          storageStatus: 'USEING'
        },
        {
          sectionId: 10000074,
          classId: 10000077,
          courseId: 10000061,
          loCode: 'ztgl_hl1',
          storageStatus: 'USEING'
        },
        {
          sectionId: 10000081,
          classId: 10000082,
          courseId: 10000061,
          loCode: 'wl_lx_ghgl_s007',
          storageStatus: 'USEING'
        },
        {
          sectionId: 10000083,
          classId: 10000084,
          courseId: 10000061,
          loCode: 'wl_lx_jjxl_s004',
          storageStatus: 'USEING'
        },
        {
          sectionId: 10000083,
          classId: 10000085,
          courseId: 10000061,
          loCode: 'wl_zh_cj_ydhlsy',
          storageStatus: 'USEING'
        },
        {
          sectionId: 10000086,
          classId: 10000087,
          courseId: 10000061,
          loCode: 'wl_zh_zt_ghglckt',
          storageStatus: 'USEING'
        },
        {
          sectionId: 10000089,
          classId: 10000090,
          courseId: 10000061,
          loCode: 'wl_lx_gg_s004',
          storageStatus: 'USEING'
        }
      ]
    },

    changePage(page) {
      this.pagination.pageIndex = page
      this.queryList()
    },

    changeCurrSize(size) {
      this.pagination.currSize = size
      this.pagination.pageIndex = 1
      this.queryList()
    },

    resetInput() {
      this.filter.courseId = ''
      this.filter.sectionId = ''
      this.filter.loCode = ''
      this.filter.textBook = ''
      this.pagination.pageIndex = 1
      this.data = []
      this.pagination.total = 0
      this.pagination.realSize = 0
    }
  }
}
</script>

<style lang="less" scoped>
@import './course-section-statistics.less';
</style>
