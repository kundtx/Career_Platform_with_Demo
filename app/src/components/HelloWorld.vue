<template>
  <el-container id="app-container">
    <el-header height="35px">Career Platform Demo</el-header>
    <el-container>
      <el-aside width="240px">
        <!-- 左边栏导航目录-->
        <el-menu :default-openeds="['1']" :unique-opened="true" active-text-color="#5C307D">
          <!-- DEMO-->
          <el-submenu index="1" :show-timeout="0" :hide-timeout="0">
            <template slot="title">
              <i class="el-icon-coordinate"></i>
              <span>DEMO</span>
            </template>
            <a :href="'#career-analysis'" style="text-decoration: none;">
              <el-menu-item index="1-1" style="font-size: 12px; height: 25px; line-height: 25px">Resume Analysis</el-menu-item>
            </a>
            <a :href="'#career-octree-visualization'" style="text-decoration: none;">
              <el-menu-item index="1-2" style="font-size: 12px; height: 25px; line-height: 25px">OCTree Visualization
              </el-menu-item>
            </a>
            <a :href="'#career-csn-visualization'" style="text-decoration: none;">
              <el-menu-item index="1-3" style="font-size: 12px; height: 25px; line-height: 25px">CSN Visualization</el-menu-item>
            </a>
          </el-submenu>

          <el-card class="box-card">
            <div class="text item" style="font-size:14px">
              Welcome! Simply enter a list of Chinese resumes separated by the # like the sample text we provided and our system will analyze the working experiences of each person, providing you with segmentation and visualization results.
              
              You can then explore the part of the octree and career social network by clicking on the corresponding buttons below. This system is designed to help you gain insights into how our project works.
            </div>
          </el-card>

        </el-menu>
      </el-aside>

      <el-main>
        <el-container class="api-cell" :id="'career-analysis'" direction="vertical">
          <el-row>
            <el-col :span="24">
              <div class="grid-content bg-purple-dark">Resume Analysis</div>
            </el-col>
          </el-row>
          <el-row :gutter="20" type="flex" justify="center">
            <el-col :span="12">
              <div>Resumes:</div>
              <el-input type="textarea" :rows="20" v-model="careerInput" placeholder="请输入内容"></el-input>
              <el-button @click="analysisRequestPost" class="api-cell-quickTry-sendPost">
                Start Analysis<i style="margin: 0;" class="el-icon-arrow-right el-icon--right"></i>
              </el-button>
            </el-col>
            <el-col :span="12">
              <div>Results:</div>
              <el-input type="textarea" :rows="20" :value="careerOutput" placeholder="分析结果" readonly></el-input>
            </el-col>
          </el-row>
        </el-container>
        <el-row>
          <el-col :span="24"><div class="grid-content bg-purple-dark"></div></el-col>
        </el-row>
        <el-container class="api-cell" :id="'career-octree-visualization'" direction="vertical">
          <el-col :span="24">
            <div class="grid-content bg-purple-dark">OCTree Visualization</div>
          </el-col>
          <div style="width:100vw;height:100vh">
            <div ref="graphOctree" style="width:100vw;height:100vh" />
          </div>
          <el-button @click="getVisualOctree" class="api-cell-quickTry-sendPost">
            Synchronize Data<i style="margin: 0;" class="el-icon-arrow-right el-icon--right"></i>
          </el-button>
        </el-container>
        <el-row>
          <el-col :span="24"><div class="grid-content bg-purple-dark"></div></el-col>
        </el-row>
        <el-container class="api-cell" :id="'career-csn-visualization'" direction="vertical">
          <el-col :span="24">
            <div class="grid-content bg-purple-dark">CSN Visualization</div>
          </el-col>
          <div style="width:100vw;height:100vh">
            <div ref="graphCSN" style="width:100vw;height:100vh" />
          </div>
          <el-button @click="getVisualCSN" class="api-cell-quickTry-sendPost">
            Synchronize Data<i style="margin: 0;" class="el-icon-arrow-right el-icon--right"></i>
          </el-button>
        </el-container>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
const neo4j = require("neo4j-driver")

export default {
  name: 'HelloWorld',
  data () {
    return {
      careerInput: '',
      careerOutput: '',
    }
  },
  mounted() {
  },
  methods: {
    analysisRequestPost() {
      const url = '/analysis'
      var content = {}
      content.txt = this.careerInput
      this.$axios.post(url, content)
        .then((response) => {
          this.careerOutput = response.data.result.join("\n")
        })
    },
    getVisualOctree() {
      const url = '/visual_octree'
      this.$axios.get(url)
        .then((response) => {
          let echartsData, nodesRelation
          let echartsNode = []
          echartsData = response.data.echartsData
          nodesRelation = response.data.nodesRelation

          var arrId = []
          var legend = []
          for (var item of echartsData) {
            legend.push({ name: item.category })
            if (arrId.indexOf(item.name) == -1) {
              arrId.push(item.name)
              echartsNode.push(item)
            }
          }

          let category
          category = Array.from(new Set(legend))

          let options
          options = {
            tooltip: {//弹窗
              show: false,
              // enterable: true,//鼠标是否可进入提示框浮层中
              // formatter: formatterHover,//修改鼠标悬停显示的内容
            },
            legend: {
              type: 'scroll',
              orient: 'vertical',
              left: 10,
              top: 20,
              bottom: 20,
              data: category
            },
            series: [
              {
                categories: category,
                type: "graph",
                layout: "force",
                zoom: 0.6,
                symbolSize: 60,
                // 节点是否可以拖动
                draggable: true,
                roam: true,
                hoverAnimation: false,
                legendHoverLink: false,
                nodeScaleRatio: 0.6, //鼠标漫游缩放时节点的相应缩放比例，当设为0时节点不随着鼠标的缩放而缩放
                focusNodeAdjacency: false, //是否在鼠标移到节点上的时候突出显示节点以及节点的边和邻接节点。
                // categories: categories,
                itemStyle: {
                  // color: "#67A3FF",
                },
                edgeSymbol: ["", "arrow"],
                // edgeSymbolSize: [80, 10],
                edgeLabel: {
                  normal: {
                    show: true,
                    textStyle: {
                      fontSize: 12,
                    },
                    formatter (x) {
                      return x.data.name;
                    },
                  },
                },
                label: {
                  normal: {
                    show: true,
                    textStyle: {
                      fontSize: 12,
                    },
                    color: "#f6f6f6",
                    textBorderColor: '#67A3FF',
                    textBorderWidth: '1.3',
                    // 多字换行
                    formatter: function (params) {
                      // console.log(params);
                      var newParamsName = "";
                      var paramsNameNumber = params.name.length;
                      var provideNumber = 7; //一行显示几个字
                      var rowNumber = Math.ceil(paramsNameNumber / provideNumber);
                      if (paramsNameNumber > provideNumber) {
                        for (var p = 0; p < rowNumber; p++) {
                          var tempStr = "";
                          var start = p * provideNumber;
                          var end = start + provideNumber;
                          if (p == rowNumber - 1) {
                            tempStr = params.name.substring(start, paramsNameNumber);
                          } else {
                            tempStr = params.name.substring(start, end) + "\n\n";
                          }
                          newParamsName += tempStr;
                        }
                      } else {
                        newParamsName = params.name;
                      }
                      return newParamsName;
                    },
                  },
                },
                force: {
                  repulsion: 200, // 节点之间的斥力因子。支持数组表达斥力范围，值越大斥力越大。
                  gravity: 0.01, // 节点受到的向中心的引力因子。该值越大节点越往中心点靠拢。
                  edgeLength: 400, // 边的两个节点之间的距离，这个距离也会受 repulsion影响 。值越大则长度越长
                  layoutAnimation: true, // 因为力引导布局会在多次迭代后才会稳定，这个参数决定是否显示布局的迭代动画
                  // 在浏览器端节点数据较多（>100）的时候不建议关闭，布局过程会造成浏览器假死。
                },
                data: echartsNode,
                links: nodesRelation,
                // categories: this.categories
              }
            ]
          }

          let myChart = this.$echarts.init(this.$refs.graphOctree)
          myChart.setOption(options)
        })
    },
    getVisualCSN() {
      const url = '/visual_csn'
      this.$axios.get(url)
        .then((response) => {
          let echartsData, nodesRelation
          let echartsNode = []
          echartsData = response.data.echartsData
          nodesRelation = response.data.nodesRelation

          var arrId = []
          var legend = []
          for (var item of echartsData) {
            legend.push({ name: item.category })
            if (arrId.indexOf(item.name) == -1) {
              arrId.push(item.name)
              echartsNode.push(item)
            }
          }

          let category
          category = Array.from(new Set(legend))

          let options
          options = {
            tooltip: {//弹窗
              show: false,
              // enterable: true,//鼠标是否可进入提示框浮层中
              // formatter: formatterHover,//修改鼠标悬停显示的内容
            },
            legend: {
              type: 'scroll',
              orient: 'vertical',
              left: 10,
              top: 20,
              bottom: 20,
              data: category
            },
            series: [
              {
                categories: category,
                type: "graph",
                layout: "force",
                zoom: 0.6,
                symbolSize: 60,
                // 节点是否可以拖动
                draggable: true,
                roam: true,
                hoverAnimation: false,
                legendHoverLink: false,
                nodeScaleRatio: 0.6, //鼠标漫游缩放时节点的相应缩放比例，当设为0时节点不随着鼠标的缩放而缩放
                focusNodeAdjacency: false, //是否在鼠标移到节点上的时候突出显示节点以及节点的边和邻接节点。
                // categories: categories,
                itemStyle: {
                  // color: "#67A3FF",
                },
                edgeSymbol: ["", "arrow"],
                // edgeSymbolSize: [80, 10],
                edgeLabel: {
                  normal: {
                    show: true,
                    textStyle: {
                      fontSize: 12,
                    },
                    formatter (x) {
                      console.log(x.data);
                      return x.data.name;
                    },
                  },
                },
                label: {
                  normal: {
                    show: true,
                    textStyle: {
                      fontSize: 12,
                    },
                    color: "#f6f6f6",
                    textBorderColor: '#67A3FF',
                    textBorderWidth: '1.3',
                    // 多字换行
                    formatter: function (params) {
                      // console.log(params);
                      var newParamsName = "";
                      var paramsNameNumber = params.name.length;
                      var provideNumber = 7; //一行显示几个字
                      var rowNumber = Math.ceil(paramsNameNumber / provideNumber);
                      if (paramsNameNumber > provideNumber) {
                        for (var p = 0; p < rowNumber; p++) {
                          var tempStr = "";
                          var start = p * provideNumber;
                          var end = start + provideNumber;
                          if (p == rowNumber - 1) {
                            tempStr = params.name.substring(start, paramsNameNumber);
                          } else {
                            tempStr = params.name.substring(start, end) + "\n\n";
                          }
                          newParamsName += tempStr;
                        }
                      } else {
                        newParamsName = params.name;
                      }
                      return newParamsName;
                    },
                  },
                },
                force: {
                  repulsion: 200, // 节点之间的斥力因子。支持数组表达斥力范围，值越大斥力越大。
                  gravity: 0.01, // 节点受到的向中心的引力因子。该值越大节点越往中心点靠拢。
                  edgeLength: 400, // 边的两个节点之间的距离，这个距离也会受 repulsion影响 。值越大则长度越长
                  layoutAnimation: true, // 因为力引导布局会在多次迭代后才会稳定，这个参数决定是否显示布局的迭代动画
                  // 在浏览器端节点数据较多（>100）的时候不建议关闭，布局过程会造成浏览器假死。
                },
                data: echartsNode,
                links: nodesRelation,
                // categories: this.categories
              }
            ]
          }

          let myChart = this.$echarts.init(this.$refs.graphCSN)
          myChart.setOption(options)
        })
    },
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
html, body, #app, #app-container {
  height: 100%;
  width: 100%;
  padding: 0;
  margin: 0;
}

.el-header {
  background-color: #5C307D;
  color: #E0E0E0;
  text-align: left;
  line-height: 35px;
  font-size: x-large;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  overflow: hidden;
  z-index: 999;
}

.el-aside {
  position: fixed;
  left: 0;
  top: 35px;
  bottom: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
  z-index: 998;
}

.el-main {
  background-color: #F9F9F9;
  color: #333;
  padding: 12px;
  position: absolute;
  top: 35px;
  left: 240px;
  right: 0;
  bottom: 0;
  overflow-y: scroll;
}

.el-menu {
  height: 100%;
  width: 100%;
  background-color: #e5daed;
  color: #333;
}

.el-submenu__title:hover {
  background-color: #e5daed !important;
}

.el-menu-item:hover {
  background-color: #fbf6ff !important;
}

.el-menu-item.is-active {
  background-color: #e5daed !important;
}

.bg-purple {
  background: #d3dce6;
}

.bg-purple-light {
  background: #e5e9f2;
}

.grid-content {
  border-radius: 4px;
  min-height: 36px;
}

.api-cell-quickTry-req {
  padding-right: 5px;
}
</style>
