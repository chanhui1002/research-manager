<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1 class="app-title">科研成果管理系统</h1>
      <el-menu
        :default-active="$route.path"
        mode="horizontal"
        router
        class="nav-menu"
        :ellipsis="false"
      >
        <el-menu-item index="/papers">
          <el-icon><Document /></el-icon>
          <span>论文</span>
        </el-menu-item>
        <el-menu-item index="/books">
          <el-icon><Reading /></el-icon>
          <span>专著</span>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <span>项目</span>
        </el-menu-item>
        <el-menu-item index="/awards">
          <el-icon><Trophy /></el-icon>
          <span>奖励</span>
        </el-menu-item>
        <el-menu-item index="/adoptions">
          <el-icon><Stamp /></el-icon>
          <span>采纳证明</span>
        </el-menu-item>
        <el-menu-item index="/honors">
          <el-icon><Medal /></el-icon>
          <span>荣誉称号</span>
        </el-menu-item>
        <el-menu-item index="/trainings">
          <el-icon><Notebook /></el-icon>
          <span>培训证明</span>
        </el-menu-item>
        <el-menu-item index="/export">
          <el-icon><Download /></el-icon>
          <span>导出</span>
        </el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }

.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.app-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  height: auto !important;
  flex-wrap: wrap;
}
.app-title {
  font-size: 18px;
  color: #303133;
  white-space: nowrap;
}
.nav-menu {
  border-bottom: none !important;
  flex: 1;
}
.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 10px;
    gap: 8px;
  }
  .app-title { font-size: 16px; }
  .nav-menu { width: 100%; overflow-x: auto; }
  .app-main { padding: 10px; }
}
</style>
