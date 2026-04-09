<template>
  <div class="bom-container">
    <el-card class="table-panel">
      <div class="table-operations" style="margin-bottom: 10px;">
        <el-button-group>
          <el-button type="success" @click="showAddRelationDialog">增加</el-button>
          <el-button type="danger" @click="removeSelectedRelations" :disabled="!selectedRows.length">
            移去 <span v-if="selectedRows.length">({{ selectedRows.length }})</span>
          </el-button>
        </el-button-group>
        <el-button type="primary" style="margin-left: 16px;" @click="saveAllChanges">保存</el-button>
      </div>
      <el-table
        v-loading="loading"
        :data="treeTableData"
        row-key="id"
        border
        style="width: 100%"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        default-expand-all
        @selection-change="handleSelectionChange"
        element-loading-text="加载中..."
        element-loading-spinner="el-icon-loading"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="code" label="编码" width="140" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="spec" label="规格" />
        <el-table-column label="数量" width="160">
          <template #default="scope">
            <template v-if="scope.row.parent_component === null || scope.row.parent_component === undefined">
              <span>{{ scope.row.quantity }}</span>
            </template>
            <template v-else>
              <el-input-number
                v-model="scope.row.quantity"
                :min="0.001"
                :precision="3"
                :step="0.001"
                :controls-position="'right'"
                @change="(value) => syncQuantity(scope.row, value)"
              />
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 增加关系弹窗 -->
    <el-dialog v-model="addRelationDialogVisible" title="增加子产品" width="500px">
      <el-form :model="relationForm" label-width="100px">
        <el-form-item label="选择产品" required>
          <el-select v-model="relationForm.selectedProduct" filterable placeholder="请选择产品">
            <el-option
              v-for="item in availableProducts"
              :key="item.id"
              :label="item.code + ' - ' + item.name"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" required>
          <el-input-number 
            v-model="relationForm.quantity" 
            :min="0.001"
            :precision="3"
            :step="0.001"
            :controls-position="'right'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addRelationDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addRelation">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'

// 路由
const route = useRoute()

// 状态管理
const loading = ref(false)
const product = ref(null)
const bomItems = ref([])
const selectedRows = ref([])

// 通用错误处理
const handleError = (error, message = '操作失败') => {
  console.error(message, error)
  ElMessage.error(message + '：' + (error.response?.data?.detail || error.message))
}

// 使用计算属性构建树形结构
const treeTableData = computed(() => {
  if (!product.value || !bomItems.value.length) return []
  const map = new Map()
  
  // 构建节点映射
  bomItems.value.forEach(item => {
    map.set(item.component, {
      id: item.component,
      code: item.component_code,
      name: item.component_name,
      quantity: item.quantity,
      parent_component: item.parent_component ?? product.value.id,
      children: []
    })
  })
  
  // 构建树形结构
  const roots = []
  map.forEach((node, key) => {
    if (node.parent_component === product.value.id) {
      roots.push(node)
    } else {
      const parent = map.get(node.parent_component)
      if (parent) {
        parent.children.push(node)
      }
    }
  })

  // 返回带根节点的完整树
  return [{
    id: product.value.id,
    code: product.value.code,
    name: product.value.name,
    quantity: 1,
    parent_component: null,
    children: roots
  }]
})

// 处理表格多选
function handleSelectionChange(selection) {
  selectedRows.value = selection
}

// 可用产品列表
const availableProducts = ref([])

// 增加关系弹窗相关
const addRelationDialogVisible = ref(false)
const relationForm = ref({
  parentItem: null, // 当前选中的父项
  selectedProduct: null,
  quantity: 1
})


// 将扁平的 bomItems 构建为树形结构（用于 TreeTable）
function buildTreeTable(items) {
  if (!product.value) return []
  // 先将所有节点放入 map
  const map = new Map()
  items.forEach(item => {
    map.set(item.component, {
      id: item.component,
      code: item.component_code,
      name: item.component_name,
      quantity: item.quantity,
      parent_component: item.parent_component ?? product.value.id, // 修正：非根节点parent_component为父id
      children: []
    })
  })
  // 构建树
  const roots = []
  map.forEach((node, key) => {
    if (node.parent_component === product.value.id) {
      roots.push(node)
    } else {
      const parent = map.get(node.parent_component)
      if (parent) {
        parent.children.push(node)
      }
    }
  })
  // 根节点前加上产品本身
  return [{
    id: product.value.id,
    code: product.value.code,
    name: product.value.name,
    quantity: 1,
    parent_component: null, // 根节点parent_component为null
    children: roots
  }]
}

// 表格数量修改 → 同步到 bomItems 和树
function syncQuantity(row, value) {
  const componentId = row.component
  // 确保数量不超过3位小数
  const qty = Number(value.toFixed(3))
  // 更新扁平数据
  const idx = bomItems.value.findIndex(i => (i.component ?? i.id) === componentId)
  if (idx !== -1) {
    bomItems.value[idx].quantity = qty
  }
  // 重新构建树表数据以保持一致
  treeTableData.value = buildTreeTable(bomItems.value)
}



// 加载可用产品列表
async function loadAvailableProducts() {
  try {
    const { data } = await api.get('bom/products/')
    if (data.results) {
      availableProducts.value = data.results.filter(p => p.id !== product.value?.id)
    }
  } catch (error) {
    console.error('加载产品列表失败:', error)
    ElMessage.error('加载产品列表失败')
  }
}

// 数据转换工具
const transformBomItem = (item) => ({
  id: item.id ?? (item.component ?? null),
  component: item.component ?? item.id ?? null,
  component_code: item.component_code ?? item.code ?? '',
  component_name: item.component_name ?? item.name ?? '',
  quantity: item.quantity ?? 1,
  parent_component: item.parent_component ?? null
})

// 加载 BOM
async function loadBom() {
  loading.value = true
  try {
    // 从路由参数获取产品ID，或使用默认值
    const productId = route.query.productId || route.params.productId
    if (!productId) {
      ElMessage.warning('请提供产品ID')
      loading.value = false
      return
    }
    const { data } = await api.get(`mpart/${productId}/`)
    
    if (!data) {
      ElMessage.warning('没有找到任何产品数据')
      return
    }

    product.value = {
      id: data.id,
      code: data.code,
      name: data.name,
      description: data.description || ''
    }

    // 处理 BOM 项
    bomItems.value = (data.bom_items || []).map(transformBomItem)

  } catch (error) {
    handleError(error, '加载失败')
  } finally {
    loading.value = false
  }
}

// 显示添加关系弹窗
function showAddRelationDialog() {
  relationForm.value.parentItem = null // 默认添加到根节点下
  relationForm.value.selectedProduct = null
  relationForm.value.quantity = 1
  addRelationDialogVisible.value = true
  loadAvailableProducts()
}

// 添加关系
async function addRelation() {
  try {
    if (!relationForm.value.selectedProduct) {
      ElMessage.error('请选择要添加的产品')
      return
    }

    const currentItems = [...bomItems.value]
    currentItems.push({
      component: relationForm.value.selectedProduct.id,
      component_code: relationForm.value.selectedProduct.code,
      component_name: relationForm.value.selectedProduct.name,
      quantity: relationForm.value.quantity,
      parent_component: relationForm.value.parentItem?.component || null
    })
    // 先本地更新
    bomItems.value = currentItems
    treeTableData.value = buildTreeTable(currentItems)

    // 更新 BOM 结构
    const payload = {
      code: product.value.code,
      name: product.value.name,
      description: product.value.description,
      bom_items: currentItems.map(i => ({
        component: i.component,
        quantity: i.quantity,
        parent_component: i.parent_component
      }))
    }

    await api.put(`bom/products/${product.value.id}/`, payload)
    ElMessage.success('添加关系成功')
    addRelationDialogVisible.value = false
    await loadBom()
  } catch (error) {
    console.error('添加关系失败:', error)
    ElMessage.error('添加关系失败：' + (error.response?.data?.detail || error.message))
  }
}

// 移除选中的关系
async function removeSelectedRelations() {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要移除的项')
    return
  }

  try {
    // 构建确认消息
    const itemNames = selectedRows.value
      .map(row => `${row.component_code} - ${row.component_name}`)
      .join('\n')

    // 确认对话框
    await ElMessageBox.confirm(
      `确定要移除以下 ${selectedRows.value.length} 个组件吗？\n${itemNames}`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )

    loading.value = true
    
    // 获取要移除的组件ID列表并更新本地数据
    const removeIds = selectedRows.value.map(row => row.component)
    bomItems.value = bomItems.value.filter(i => !removeIds.includes(i.component))
    
    // 更新后端数据
    const payload = buildSavePayload()
    await api.put(`bom/products/${product.value.id}/`, payload)
    
    ElMessage.success(`已移除 ${selectedRows.value.length} 个组件`)
    selectedRows.value = []
    
    // 刷新数据
    await loadBom()
  } catch (error) {
    if (error !== 'cancel') {
      handleError(error, '移除关系失败')
    }
  } finally {
    loading.value = false
  }
}

// 构建保存的payload
const buildSavePayload = () => ({
  code: product.value.code,
  name: product.value.name,
  description: product.value.description,
  bom_items: bomItems.value.map(i => ({
    component: i.component,
    quantity: i.quantity,
    parent_component: i.parent_component
  }))
})

// 保存所有更改
async function saveAllChanges() {
  if (!product.value) return

  loading.value = true
  try {
    const payload = buildSavePayload()
    await api.put(`bom/products/${product.value.id}/`, payload)
    
    ElMessage.success('已保存所有更改')
    // 刷新数据确保与后端同步
    await loadBom()
  } catch (error) {
    handleError(error, '保存失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadBom()
})
</script>

<style scoped>
.bom-container {
  display: flex;
  gap: 5px;
}
.tree-panel {
  width: 36%;
}
.table-panel {
  flex: 1;
}
</style>
