<script setup>
import douyinHomeScreenshot from './assets/douyin-home-root.jpg';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

gsap.registerPlugin(ScrollTrigger);

const open = ref(false);
const loading = ref(false);
const dragging = ref(false);
const activeScene = ref(0);
const overlayRef = ref(null);
const scrollRef = ref(null);
const canvasRef = ref(null);
const progressRef = ref(null);
const searchQuery = ref('');
const searchResultVisible = ref(false);
const searchDemoOpacity = ref(0);
const searchExitProgress = ref(0);
const mergeStage = ref(0);
const mergeDemoOpacity = ref(0);

const searchTargetUrl = 'aweme://search/result?keyword=性能监控';
const searchPanelStyle = computed(() => ({
  opacity: searchDemoOpacity.value,
  transform: `translate3d(${searchExitProgress.value * 96}px, ${searchExitProgress.value * 22}px, 0) scale(${1 - searchExitProgress.value * 0.18})`,
}));

let previousBodyOverflow = '';
let animationContext = null;
let renderer = null;
let scene = null;
let camera = null;
let world = null;
let resizeObserver = null;
let animationFrame = 0;
let setupVersion = 0;
let currentProgress = 0;
let cameraBaseZ = 22.5;
let targetPointerX = 0;
let targetPointerY = 0;
let pointerX = 0;
let pointerY = 0;
let dragPointerId = null;
let lastDragX = 0;
let lastDragY = 0;
let manualRotationX = 0;
let manualRotationY = 0;
let rotationVelocityX = 0;
let rotationVelocityY = 0;
let baseWorldRotationX = -0.12;
let baseWorldRotationY = 0;
let treeNodes = [];
let rootPreview = null;
let treeEdges = null;
let treeEdgeGlow = null;
let treeBranches = null;
let activeRouteBranches = null;
let activeRouteLinks = [];
let graphLinks = [];
let searchTargetNode = null;
let searchSceneProgress = 0;
let mergeSceneProgress = 0;
let mergeParentNode = null;
let mergeOrphanNode = null;
let mergeOrphanHalo = null;
let mergePathLine = null;
let mergePathGlow = null;
let mergeFinalLine = null;
let mergePathCurve = null;
let mergeImpactRing = null;
let mergeOrbitRings = [];
let mergeTrailParticles = [];
let activeRouteNodeOrders = new Set();
let activeRouteEdgeIndexes = new Set();
let movingSignals = [];
let injectionBeams = [];
let starField = null;
let threeApi = null;

const scenes = [
  {
    id: 'prelude',
    number: '00',
    kicker: 'RAW SIGNALS / HDC FITTING',
    title: '散落的页面，第一次被组织起来',
    text: '起初只有 HDC 捕获的 URL、截图和控件证据，它们彼此独立，尚未形成关系。设备连接、页面识别与跳转回放逐步补全上下文，散点开始寻找父子关系，最终拟合为一棵可持续生长的应用图谱树。',
    tags: ['HDC 采集', '页面识别', '关系拟合'],
    metric: 'SIGNAL → TREE',
    metricLabel: '从离散证据到结构化图谱',
    side: 'left',
  },
  {
    id: 'origin',
    number: '01',
    kicker: 'THE FIRST MAP',
    title: '从第一张截图，长出一棵图谱树',
    text: '最初，我们只想回答一个简单的问题：用户从哪个页面，通过哪个控件，到达了哪里。页面成为节点，操作成为边，散落在手机里的路径第一次拥有了形状。',
    tags: ['页面节点', '控件边关系', '真实截图'],
    metric: '1 → 300+',
    metricLabel: '从原型到规模化页面',
    side: 'left',
  },
  {
    id: 'exploration',
    number: '02',
    kicker: 'URL SEARCH / AI LOCATE',
    title: '输入一个 URL，图谱定位它所代表的页面',
    text: '监控返回的高危 URL 被输入图谱。系统先完成精确与归一化匹配，再由大模型结合截图、页面文本和动作结构解释命中结果，让一个抽象地址重新变成可以查看、验证与执行的真实页面。',
    tags: ['URL 定位', '节点高亮', '多模态分析'],
    metric: 'URL → PAGE',
    metricLabel: '从风险地址定位到页面证据',
    side: 'right',
  },
  {
    id: 'node-merge',
    number: '03',
    kicker: 'ORPHAN NODE / GRAPH MERGE',
    title: '发现新页面，把它可靠地接回主树',
    text: '一个新 URL 先以游离节点建档，截图经过多模态模型补全页面摘要、embedding_text 与动作信息。系统给出候选父节点，确认无环后生成新边，页面从“待归属证据”正式成为主树的一部分。',
    tags: ['创建节点', 'AI 信息补全', '无环合并'],
    metric: 'ORPHAN → TREE',
    metricLabel: '创建、确认父节点、写入边关系',
    side: 'left',
  },
  {
    id: 'scene-function',
    number: '04',
    kicker: 'SCENARIO FUNCTION MAPPING',
    title: '场景功能，逐项指向对应页面',
    text: '登录、注册、点赞与收藏不再以杂乱光束注入。每个场景功能都通过语义匹配连接到明确的页面节点，让功能清单、页面证据与覆盖状态形成直观的一对一映射。',
    tags: ['功能清单', '页面定位', '覆盖映射'],
    metric: '4 SCENES',
    metricLabel: '四类典型场景功能已定位',
    side: 'right',
  },
  {
    id: 'test-case',
    number: '05',
    kicker: 'TEST CASE ORCHESTRATION',
    title: '用例从右侧抵达，路径被赋予任务',
    text: '从 root 到末端的每条路径都能成为覆盖用例；任意节点也能组合滑动、长按和回退。右侧注入的不是静态脚本，而是一批能沿图谱执行、采集和复盘的测试意图。',
    tags: ['全路径覆盖', '典型动作组合', '按需生成'],
    metric: 'PATH × ACTION',
    metricLabel: '页面路径与动作组合',
    side: 'right',
  },
  {
    id: 'observability',
    number: '06',
    kicker: 'LIVE OBSERVABILITY',
    title: '执行数据回流，当前路线被点亮',
    text: '高危 URL 触发按需用例，脚本沿当前路径复现用户行为。功耗、帧率、耗时与异常结果沿边回流，当前路线持续发光，其他分支同步降亮，让每一次抵达都可追溯。',
    tags: ['周期趋势', 'URL 告警', '证据回流'],
    metric: 'URL → REPORT',
    metricLabel: '从告警到可复盘报告',
    side: 'left',
  },
  {
    id: 'platform',
    number: '07',
    kicker: 'CONTINUOUS APP INTELLIGENCE',
    title: '它不再只是一张图，而是持续生长的应用认知',
    text: '游离页面、人工证据、AI 推断、场景功能、测试用例与性能结果共享同一棵树。每一次采集都补充认知，每一次复核都提高可信度，每一次执行都让下一次探索更聪明。',
    tags: ['持续覆盖', '人机共审', '图谱治理'],
    metric: '8 STAGES',
    metricLabel: '从图谱原型走向工程平台',
    side: 'right',
  },
];

const scenarioFunctions = [
  { name: '登录', code: 'LOGIN', target: '账号登录页', color: '#0b63ce' },
  { name: '注册', code: 'REGISTER', target: '账号注册页', color: '#1677ff' },
  { name: '点赞', code: 'LIKE', target: '内容详情页', color: '#47a5ff' },
  { name: '收藏', code: 'FAVORITE', target: '收藏列表页', color: '#78baff' },
];

function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value));
}

function smoothstep(value) {
  const normalized = clamp(value);
  return normalized * normalized * (3 - 2 * normalized);
}

async function openJourney() {
  open.value = true;
  loading.value = true;
  activeScene.value = 0;
  currentProgress = 0;
  manualRotationX = 0;
  manualRotationY = 0;
  rotationVelocityX = 0;
  rotationVelocityY = 0;
  searchSceneProgress = 0;
  searchQuery.value = '';
  searchResultVisible.value = false;
  searchDemoOpacity.value = 0;
  searchExitProgress.value = 0;
  mergeSceneProgress = 0;
  mergeStage.value = 0;
  mergeDemoOpacity.value = 0;
  previousBodyOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  await nextTick();
  overlayRef.value?.focus();
  setupScrollStory();
  const version = ++setupVersion;
  try {
    await setupThreeScene(version);
  } finally {
    if (version === setupVersion) loading.value = false;
  }
}

function closeJourney() {
  setupVersion += 1;
  destroyJourney();
  document.body.style.overflow = previousBodyOverflow;
  open.value = false;
}

function destroyJourney() {
  animationContext?.revert();
  animationContext = null;
  resizeObserver?.disconnect();
  resizeObserver = null;
  cancelAnimationFrame(animationFrame);
  animationFrame = 0;

  if (scene) {
    scene.traverse((object) => {
      object.geometry?.dispose?.();
      if (Array.isArray(object.material)) {
        object.material.forEach((material) => {
          material.map?.dispose?.();
          material.dispose?.();
        });
      } else {
        object.material?.map?.dispose?.();
        object.material?.dispose?.();
      }
    });
  }
  renderer?.dispose?.();
  renderer = null;
  scene = null;
  camera = null;
  world = null;
  treeNodes = [];
  rootPreview = null;
  treeEdges = null;
  treeEdgeGlow = null;
  treeBranches = null;
  activeRouteBranches = null;
  graphLinks = [];
  activeRouteNodeOrders = new Set();
  activeRouteEdgeIndexes = new Set();
  activeRouteLinks = [];
  searchTargetNode = null;
  searchSceneProgress = 0;
  mergeSceneProgress = 0;
  mergeParentNode = null;
  mergeOrphanNode = null;
  mergeOrphanHalo = null;
  mergePathLine = null;
  mergePathGlow = null;
  mergeFinalLine = null;
  mergePathCurve = null;
  mergeImpactRing = null;
  mergeOrbitRings = [];
  mergeTrailParticles = [];
  movingSignals = [];
  injectionBeams = [];
  starField = null;
  threeApi = null;
}

function setupScrollStory() {
  animationContext?.revert();
  animationContext = gsap.context(() => {
    const sections = gsap.utils.toArray('.journey-section');
    gsap.set(progressRef.value, { scaleX: 0, transformOrigin: 'left center' });

    ScrollTrigger.create({
      scroller: scrollRef.value,
      trigger: '.journey-story',
      start: 'top top',
      end: 'bottom bottom',
      scrub: 0.7,
      onUpdate: (self) => {
        currentProgress = self.progress;
        updateThreeScene(currentProgress);
        gsap.set(progressRef.value, { scaleX: self.progress });
      },
    });

    sections.forEach((section, index) => {
      const copy = section.querySelector('.journey-copy');
      const metric = section.querySelector('.journey-metric');
      const direction = section.dataset.side === 'right' ? 1 : -1;

      gsap.timeline({
        scrollTrigger: {
          scroller: scrollRef.value,
          trigger: section,
          start: 'top 78%',
          end: 'bottom 22%',
          scrub: 0.8,
          onEnter: () => { activeScene.value = index; },
          onEnterBack: () => { activeScene.value = index; },
          onUpdate: (self) => {
            if (scenes[index].id === 'exploration') updateSearchDemo(self.progress);
            if (scenes[index].id === 'node-merge') updateMergeDemo(self.progress);
          },
        },
      })
        .fromTo(copy, { x: direction * 110, opacity: 0.08 }, { x: 0, opacity: 1, duration: 0.35, ease: 'none' })
        .fromTo(metric, { y: 34, opacity: 0 }, { y: 0, opacity: 1, duration: 0.2, ease: 'none' }, '<0.08')
        .to(copy, { x: direction * -34, opacity: 0.18, duration: 0.3, ease: 'none' }, 0.72)
        .to(metric, { opacity: 0, duration: 0.18, ease: 'none' }, 0.78);
    });

    ScrollTrigger.refresh();
  }, overlayRef.value);
}

function updateSearchDemo(progress) {
  searchSceneProgress = clamp(progress);
  const typingProgress = clamp((progress - 0.12) / 0.34);
  const characterCount = Math.floor(searchTargetUrl.length * typingProgress);
  searchQuery.value = searchTargetUrl.slice(0, characterCount);
  searchResultVisible.value = progress >= 0.48;
  searchDemoOpacity.value = progress < 0.08
    ? progress / 0.08
    : progress > 0.8
      ? 1 - clamp((progress - 0.8) / 0.18)
      : 1;
  searchExitProgress.value = clamp((progress - 0.78) / 0.2);
  updateThreeScene(currentProgress);
}

function updateMergeDemo(progress) {
  mergeSceneProgress = clamp(progress);
  mergeStage.value = progress < 0.3 ? 0 : progress < 0.64 ? 1 : progress < 0.86 ? 2 : 3;
  mergeDemoOpacity.value = progress < 0.08
    ? progress / 0.08
    : progress > 0.88
      ? 1 - clamp((progress - 0.88) / 0.11)
      : 1;
  updateThreeScene(currentProgress);
}

function scrollToScene(index) {
  const section = overlayRef.value?.querySelectorAll('.journey-section')?.[index];
  section?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function handleKeydown(event) {
  if (event.key === 'ArrowDown' || event.key === 'PageDown') {
    event.preventDefault();
    scrollToScene(Math.min(scenes.length - 1, activeScene.value + 1));
  }
  if (event.key === 'ArrowUp' || event.key === 'PageUp') {
    event.preventDefault();
    scrollToScene(Math.max(0, activeScene.value - 1));
  }
}

function handlePointerMove(event) {
  if (dragging.value && event.pointerId === dragPointerId) {
    const deltaX = event.clientX - lastDragX;
    const deltaY = event.clientY - lastDragY;
    lastDragX = event.clientX;
    lastDragY = event.clientY;
    rotationVelocityY = deltaX * 0.006;
    rotationVelocityX = deltaY * 0.004;
    manualRotationY += rotationVelocityY;
    manualRotationX = clamp(manualRotationX + rotationVelocityX, -0.72, 0.72);
    return;
  }
  targetPointerX = (event.clientX / window.innerWidth - 0.5) * 2;
  targetPointerY = (event.clientY / window.innerHeight - 0.5) * 2;
}

function handlePointerDown(event) {
  if (event.pointerType !== 'mouse' || event.button !== 0) return;
  if (event.target.closest?.('button, .journey-copy, .journey-header')) return;
  dragging.value = true;
  dragPointerId = event.pointerId;
  lastDragX = event.clientX;
  lastDragY = event.clientY;
  rotationVelocityX = 0;
  rotationVelocityY = 0;
  overlayRef.value?.setPointerCapture?.(event.pointerId);
}

function handlePointerUp(event) {
  if (event.pointerId !== dragPointerId) return;
  dragging.value = false;
  overlayRef.value?.releasePointerCapture?.(event.pointerId);
  dragPointerId = null;
}

function resetTreeView() {
  gsap.to({ x: manualRotationX, y: manualRotationY }, {
    x: 0,
    y: 0,
    duration: 0.7,
    ease: 'power3.out',
    onUpdate() {
      manualRotationX = this.targets()[0].x;
      manualRotationY = this.targets()[0].y;
    },
  });
  rotationVelocityX = 0;
  rotationVelocityY = 0;
}

async function setupThreeScene(version) {
  const THREE = await import('three');
  if (version !== setupVersion || !canvasRef.value) return;
  threeApi = THREE;

  renderer = new THREE.WebGLRenderer({
    canvas: canvasRef.value,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  });
  renderer.setClearColor(0xf4f8fd, 1);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0xf4f8fd, 0.032);
  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(0, 0.5, 20);

  world = new THREE.Group();
  world.rotation.x = -0.12;
  scene.add(world);

  createStarField(THREE);
  createGraphTree(THREE);
  createNodeMergeDemo(THREE);
  createInjectionBeams(THREE, 'left', 0x1677ff);
  createMovingSignals(THREE);

  const cyanLight = new THREE.PointLight(0x1677ff, 15, 35, 2);
  cyanLight.position.set(-8, 5, 8);
  scene.add(cyanLight);
  resizeRenderer();
  resizeObserver = new ResizeObserver(resizeRenderer);
  resizeObserver.observe(overlayRef.value);
  updateThreeScene(currentProgress);
  renderFrame();
}

function createStarField(THREE) {
  const positions = [];
  for (let index = 0; index < 720; index += 1) {
    const radius = 18 + (index % 37) * 0.62;
    const angle = index * 2.399963;
    positions.push(
      Math.cos(angle) * radius,
      ((index * 47) % 97) / 97 * 32 - 16,
      Math.sin(angle) * radius - 14,
    );
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    color: 0x8eafd0,
    size: 0.035,
    transparent: true,
    opacity: 0.5,
    depthWrite: false,
  });
  starField = new THREE.Points(geometry, material);
  scene.add(starField);
}

function createGraphTree(THREE) {
  const nodeGeometry = new THREE.SphereGeometry(0.088, 12, 10);
  const haloGeometry = new THREE.SphereGeometry(0.16, 10, 8);
  const edgePositions = [];
  const domainCount = 6;

  function addNode(position, level, parent = null, channel = 0, scale = 1) {
    const order = treeNodes.length;
    const scatterAngle = order * 2.399963 + (order % 5) * 0.19;
    const scatterRadius = 2.6 + (order % 19) * 0.39;
    const scatterPosition = new THREE.Vector3(
      Math.cos(scatterAngle) * scatterRadius,
      -5.2 + ((order * 37) % 101) / 100 * 10.4,
      Math.sin(scatterAngle) * (1.2 + (order % 9) * 0.34) + ((order % 3) - 1) * 0.45,
    );
    const material = new THREE.MeshBasicMaterial({
      color: level === 0 ? 0x0b63ce : 0x1677ff,
      transparent: true,
      opacity: 0.98,
      blending: THREE.NormalBlending,
      depthWrite: false,
    });
    const node = new THREE.Mesh(nodeGeometry, material);
    node.position.copy(position);
    node.scale.setScalar(scale);
    node.userData = {
      order,
      level,
      baseScale: scale,
      phase: order * 0.47 + level,
      channel,
      parent,
      linkIndex: null,
      halo: null,
      treePosition: position.clone(),
      scatterPosition,
    };

    if (level <= 2) {
      const halo = new THREE.Mesh(haloGeometry, new THREE.MeshBasicMaterial({
        color: level === 0 ? 0x65aaff : 0x8ac5ff,
        transparent: true,
        opacity: level === 0 ? 0.24 : 0.13,
        blending: THREE.NormalBlending,
        depthWrite: false,
      }));
      halo.scale.setScalar(level === 0 ? 2.15 : 1.35);
      node.add(halo);
      node.userData.halo = halo;
    }

    treeNodes.push(node);
    world.add(node);

    if (parent) {
      edgePositions.push(
        parent.position.x, parent.position.y, parent.position.z,
        position.x, position.y, position.z,
      );
      const linkIndex = graphLinks.length;
      graphLinks.push({
        from: parent.position.clone(),
        to: position.clone(),
        channel,
        parent,
        target: node,
      });
      node.userData.linkIndex = linkIndex;
    }
    return node;
  }

  const root = addNode(new THREE.Vector3(0, 5.35, 0), 0, null, 0, 2.45);
  createRootPreview(THREE, root);
  const hub = addNode(new THREE.Vector3(0, 3.85, 0), 1, root, 0, 1.85);
  const domains = [];

  for (let domainIndex = 0; domainIndex < domainCount; domainIndex += 1) {
    const baseAngle = domainIndex / domainCount * Math.PI * 2 - Math.PI / 2;
    const domain = addNode(new THREE.Vector3(
      Math.cos(baseAngle) * 2.15,
      1.82 - Math.sin(domainIndex * 1.4) * 0.12,
      Math.sin(baseAngle) * 0.9,
    ), 2, hub, domainIndex, 1.58);
    domains.push({ node: domain, angle: baseAngle, domainIndex });
  }

  const sections = [];
  domains.forEach(({ node: domain, angle: baseAngle, domainIndex }) => {
    [-0.24, 0, 0.24].forEach((offset, childIndex) => {
      const angle = baseAngle + offset;
      const section = addNode(new THREE.Vector3(
        Math.cos(angle) * 4.25,
        -0.42 - childIndex * 0.12,
        Math.sin(angle) * 1.72,
      ), 3, domain, domainIndex, 1.28);
      sections.push({ node: section, angle, domainIndex, childIndex });
    });
  });

  const pages = [];
  sections.forEach(({ node: section, angle: sectionAngle, domainIndex, childIndex }) => {
    [-0.11, 0.11].forEach((offset, pageIndex) => {
      const angle = sectionAngle + offset;
      const page = addNode(new THREE.Vector3(
        Math.cos(angle) * 6.7,
        -2.58 - childIndex * 0.13 - pageIndex * 0.08,
        Math.sin(angle) * 2.8,
      ), 4, section, domainIndex, 1.08);
      pages.push({ node: page, angle, domainIndex, pageIndex });
    });
  });

  const leaves = [];
  pages.forEach(({ node: page, angle: pageAngle, domainIndex, pageIndex }) => {
    [-0.07, 0.07].forEach((offset, leafIndex) => {
      const angle = pageAngle + offset;
      const leaf = addNode(new THREE.Vector3(
        Math.cos(angle) * 9.2,
        -4.65 - pageIndex * 0.12 - leafIndex * 0.14,
        Math.sin(angle) * 3.9,
      ), 5, page, domainIndex, 0.94 + leafIndex * 0.08);
      leaves.push(leaf);
    });
  });

  let routeNode = leaves[30] || leaves[0];
  while (routeNode) {
    activeRouteNodeOrders.add(routeNode.userData.order);
    if (routeNode.userData.linkIndex !== null) {
      activeRouteEdgeIndexes.add(routeNode.userData.linkIndex);
    }
    routeNode = routeNode.userData.parent;
  }

  searchTargetNode = pages[2]?.node || sections[1]?.node || treeNodes[20];
  mergeParentNode = pages[3]?.node || sections[1]?.node || treeNodes[21];
  const searchHalo = new THREE.Mesh(
    new THREE.SphereGeometry(0.3, 14, 12),
    new THREE.MeshBasicMaterial({
      color: 0x1677ff,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  );
  searchTargetNode.add(searchHalo);
  searchTargetNode.userData.searchHalo = searchHalo;

  const edgeGeometry = new THREE.BufferGeometry();
  edgeGeometry.setAttribute('position', new THREE.Float32BufferAttribute(edgePositions, 3));
  edgeGeometry.setDrawRange(0, 0);
  treeEdges = new THREE.LineSegments(edgeGeometry, new THREE.LineBasicMaterial({
    color: 0x4b94df,
    transparent: true,
    opacity: 0.58,
    blending: THREE.NormalBlending,
    depthWrite: false,
  }));
  treeEdgeGlow = new THREE.LineSegments(edgeGeometry, new THREE.LineBasicMaterial({
    color: 0x9bc9f2,
    transparent: true,
    opacity: 0.12,
    blending: THREE.NormalBlending,
    depthWrite: false,
  }));
  treeEdgeGlow.scale.setScalar(1.008);

  const branchGeometry = new THREE.CylinderGeometry(0.022, 0.042, 1, 6, 1, true);
  const branchMaterial = new THREE.MeshBasicMaterial({
    color: 0x397fca,
    transparent: true,
    opacity: 0.34,
    blending: THREE.NormalBlending,
    depthWrite: false,
  });
  treeBranches = new THREE.InstancedMesh(branchGeometry, branchMaterial, graphLinks.length);
  treeBranches.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  activeRouteLinks = graphLinks.filter((_, index) => activeRouteEdgeIndexes.has(index));
  const routeBranchGeometry = new THREE.CylinderGeometry(0.036, 0.062, 1, 8, 1, true);
  const routeBranchMaterial = new THREE.MeshBasicMaterial({
    color: 0x075fc7,
    transparent: true,
    opacity: 0,
    blending: THREE.NormalBlending,
    depthWrite: false,
  });
  activeRouteBranches = new THREE.InstancedMesh(routeBranchGeometry, routeBranchMaterial, activeRouteLinks.length);
  activeRouteBranches.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const up = new THREE.Vector3(0, 1, 0);
  const midpoint = new THREE.Vector3();
  const direction = new THREE.Vector3();
  const quaternion = new THREE.Quaternion();
  const scale = new THREE.Vector3();
  const matrix = new THREE.Matrix4();
  graphLinks.forEach((link, index) => {
    midpoint.copy(link.from).add(link.to).multiplyScalar(0.5);
    direction.copy(link.to).sub(link.from);
    const length = direction.length();
    quaternion.setFromUnitVectors(up, direction.normalize());
    const width = index === 0 ? 2.8 : link.from.y < -2 ? 1.8 : 1;
    scale.set(width, length, width);
    matrix.compose(midpoint, quaternion, scale);
    treeBranches.setMatrixAt(index, matrix);
  });
  activeRouteLinks.forEach((link, index) => {
    midpoint.copy(link.from).add(link.to).multiplyScalar(0.5);
    direction.copy(link.to).sub(link.from);
    const length = direction.length();
    quaternion.setFromUnitVectors(up, direction.normalize());
    scale.set(1, length, 1);
    matrix.compose(midpoint, quaternion, scale);
    activeRouteBranches.setMatrixAt(index, matrix);
  });
  treeBranches.count = 0;
  world.add(treeEdgeGlow, treeBranches, treeEdges, activeRouteBranches);
}

function createNodeMergeDemo(THREE) {
  if (!mergeParentNode) return;
  const start = new THREE.Vector3(10.8, 1.1, 2.6);
  const end = mergeParentNode.userData.treePosition.clone().add(new THREE.Vector3(0.95, -1.25, 0.34));
  const control = new THREE.Vector3(7.2, 3.6, 4.8);
  mergePathCurve = new THREE.QuadraticBezierCurve3(start, control, end);

  mergeOrphanNode = new THREE.Mesh(
    new THREE.SphereGeometry(0.16, 16, 14),
    new THREE.MeshBasicMaterial({
      color: 0x1687ff,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  );
  mergeOrphanHalo = new THREE.Mesh(
    new THREE.SphereGeometry(0.42, 14, 12),
    new THREE.MeshBasicMaterial({
      color: 0x65b5ff,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  );
  const ringGeometry = new THREE.TorusGeometry(0.31, 0.012, 8, 48);
  for (let index = 0; index < 2; index += 1) {
    const ring = new THREE.Mesh(ringGeometry, new THREE.MeshBasicMaterial({
      color: index === 0 ? 0x1687ff : 0x8dcbff,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }));
    ring.rotation.x = index === 0 ? Math.PI / 2 : Math.PI / 3;
    ring.rotation.y = index === 0 ? 0 : Math.PI / 4;
    mergeOrphanNode.add(ring);
    mergeOrbitRings.push(ring);
  }
  mergeOrphanNode.add(mergeOrphanHalo);
  mergeOrphanNode.position.copy(start);
  mergeOrphanNode.visible = false;

  mergePathLine = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(mergePathCurve.getPoints(56)),
    new THREE.LineBasicMaterial({
      color: 0x2494ff,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  );
  mergePathGlow = new THREE.Line(
    mergePathLine.geometry,
    new THREE.LineBasicMaterial({
      color: 0x9bd2ff,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  mergeFinalLine = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([mergeParentNode.userData.treePosition.clone(), end]),
    new THREE.LineBasicMaterial({
      color: 0x0b6edc,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    }),
  );
  mergeImpactRing = new THREE.Mesh(
    new THREE.TorusGeometry(0.2, 0.018, 8, 48),
    new THREE.MeshBasicMaterial({
      color: 0x47a5ff,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  mergeImpactRing.position.copy(end);
  mergeImpactRing.rotation.x = Math.PI / 2;

  const particleGeometry = new THREE.SphereGeometry(0.045, 8, 7);
  for (let index = 0; index < 18; index += 1) {
    const particle = new THREE.Mesh(
      particleGeometry,
      new THREE.MeshBasicMaterial({
        color: index % 3 === 0 ? 0xc4e6ff : index % 2 === 0 ? 0x65b5ff : 0x1677ff,
        transparent: true,
        opacity: 0,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    );
    particle.visible = false;
    world.add(particle);
    mergeTrailParticles.push({ particle, delay: index * 0.034, phase: index * 0.7 });
  }
  world.add(mergePathGlow, mergePathLine, mergeFinalLine, mergeImpactRing, mergeOrphanNode);
}

function updateGraphGeometry(THREE) {
  if (!treeEdges || !treeBranches) return;
  const positions = treeEdges.geometry.attributes.position;
  const up = new THREE.Vector3(0, 1, 0);
  const midpoint = new THREE.Vector3();
  const direction = new THREE.Vector3();
  const quaternion = new THREE.Quaternion();
  const scale = new THREE.Vector3();
  const matrix = new THREE.Matrix4();

  graphLinks.forEach((link, index) => {
    link.from.copy(link.parent.position);
    link.to.copy(link.target.position);
    positions.setXYZ(index * 2, link.from.x, link.from.y, link.from.z);
    positions.setXYZ(index * 2 + 1, link.to.x, link.to.y, link.to.z);
    midpoint.copy(link.from).add(link.to).multiplyScalar(0.5);
    direction.copy(link.to).sub(link.from);
    const length = Math.max(direction.length(), 0.001);
    quaternion.setFromUnitVectors(up, direction.normalize());
    const width = index === 0 ? 2.8 : link.from.y < -2 ? 1.8 : 1;
    scale.set(width, length, width);
    matrix.compose(midpoint, quaternion, scale);
    treeBranches.setMatrixAt(index, matrix);
  });
  positions.needsUpdate = true;
  treeBranches.instanceMatrix.needsUpdate = true;
  treeEdges.geometry.computeBoundingSphere();

  activeRouteLinks.forEach((link, index) => {
    midpoint.copy(link.from).add(link.to).multiplyScalar(0.5);
    direction.copy(link.to).sub(link.from);
    const length = Math.max(direction.length(), 0.001);
    quaternion.setFromUnitVectors(up, direction.normalize());
    scale.set(1, length, 1);
    matrix.compose(midpoint, quaternion, scale);
    activeRouteBranches.setMatrixAt(index, matrix);
  });
  if (activeRouteBranches) activeRouteBranches.instanceMatrix.needsUpdate = true;
}

function createRootLabelTexture(THREE) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 144;
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = '#0b63ce';
  context.beginPath();
  context.roundRect(10, 10, 492, 124, 62);
  context.fill();
  context.strokeStyle = 'rgba(255, 255, 255, 0.92)';
  context.lineWidth = 6;
  context.stroke();
  context.fillStyle = '#ffffff';
  context.font = '700 58px Arial, sans-serif';
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText('ROOT', 256, 75);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
}

function createRootPreview(THREE, root) {
  const screenshotTexture = new THREE.TextureLoader().load(douyinHomeScreenshot);
  screenshotTexture.colorSpace = THREE.SRGBColorSpace;
  screenshotTexture.minFilter = THREE.LinearMipmapLinearFilter;
  screenshotTexture.magFilter = THREE.LinearFilter;

  const glow = new THREE.Sprite(new THREE.SpriteMaterial({
    color: 0x65aaff,
    transparent: true,
    opacity: 0.24,
    depthTest: false,
    depthWrite: false,
  }));
  const frame = new THREE.Sprite(new THREE.SpriteMaterial({
    color: 0x0b63ce,
    transparent: true,
    opacity: 0.96,
    depthTest: false,
    depthWrite: false,
  }));
  const screenshot = new THREE.Sprite(new THREE.SpriteMaterial({
    map: screenshotTexture,
    color: 0xffffff,
    transparent: true,
    opacity: 1,
    depthTest: false,
    depthWrite: false,
  }));
  const label = new THREE.Sprite(new THREE.SpriteMaterial({
    map: createRootLabelTexture(THREE),
    transparent: true,
    opacity: 1,
    depthTest: false,
    depthWrite: false,
  }));

  glow.position.copy(root.position).add(new THREE.Vector3(0, 0.22, -0.06));
  frame.position.copy(root.position).add(new THREE.Vector3(0, 0.22, -0.04));
  screenshot.position.copy(root.position).add(new THREE.Vector3(0, 0.22, 0));
  label.position.copy(root.position).add(new THREE.Vector3(0, 0.98, 0.03));
  glow.scale.set(1.56, 3.04, 1);
  frame.scale.set(1.38, 2.8, 1);
  screenshot.scale.set(1.24, 2.62, 1);
  label.scale.set(1.08, 0.3, 1);
  glow.renderOrder = 40;
  frame.renderOrder = 41;
  screenshot.renderOrder = 42;
  label.renderOrder = 43;
  world.add(glow, frame, screenshot, label);
  rootPreview = {
    root,
    glow,
    frame,
    screenshot,
    label,
    offsets: {
      glow: new THREE.Vector3(0, 0.22, -0.06),
      frame: new THREE.Vector3(0, 0.22, -0.04),
      screenshot: new THREE.Vector3(0, 0.22, 0),
      label: new THREE.Vector3(0, 0.98, 0.03),
    },
  };
}

function createInjectionBeams(THREE, side, color) {
  const direction = side === 'left' ? -1 : 1;
  const targetPool = treeNodes.filter((node) => node.userData.level === 4);
  const targetIndexes = [1, 10, 20, 30];
  const beamColors = [0x0b63ce, 0x1677ff, 0x47a5ff, 0x78baff];

  for (let index = 0; index < 4; index += 1) {
    const target = targetPool[targetIndexes[index] % targetPool.length];
    const beamColor = beamColors[index] || color;
    const start = new THREE.Vector3(direction * 11.2, 2.55 - index * 1.55, 0.8 + index * 0.25);
    const control = new THREE.Vector3(direction * 7.2, 2.1 - index * 0.85, 3.6);
    const curve = new THREE.QuadraticBezierCurve3(start, control, target.position.clone());
    const points = curve.getPoints(48);
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    geometry.setDrawRange(0, 0);
    const material = new THREE.LineBasicMaterial({
      color: beamColor,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const line = new THREE.Line(geometry, material);
    const orb = new THREE.Mesh(
      new THREE.SphereGeometry(0.105, 8, 8),
      new THREE.MeshBasicMaterial({ color: beamColor, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }),
    );
    const arrow = new THREE.Mesh(
      new THREE.ConeGeometry(0.13, 0.34, 10),
      new THREE.MeshBasicMaterial({ color: beamColor, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }),
    );
    const tangent = curve.getTangent(1).normalize();
    arrow.position.copy(target.position);
    arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
    orb.position.copy(start);
    world.add(line, orb, arrow);
    injectionBeams.push({ side, curve, line, orb, arrow, target, phase: index * 0.1, pointCount: points.length });
  }
}

function createMovingSignals(THREE) {
  const signalGeometry = new THREE.SphereGeometry(0.07, 8, 8);
  const routeLinks = graphLinks.filter((_, index) => activeRouteEdgeIndexes.has(index));
  for (let index = 0; index < 24; index += 1) {
    const link = routeLinks[index % routeLinks.length];
    const material = new THREE.MeshBasicMaterial({
      color: index % 3 === 0 ? 0x0b63ce : index % 2 === 0 ? 0x1677ff : 0x65aaff,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    });
    const signal = new THREE.Mesh(signalGeometry, material);
    signal.visible = false;
    world.add(signal);
    movingSignals.push({ signal, from: link.from.clone(), to: link.to.clone(), phase: index / 24 });
  }
}

function updateThreeScene(progress) {
  if (!threeApi || !world || !camera) return;
  const THREE = threeApi;
  const preludeEnd = 1 / scenes.length;
  const formation = smoothstep(progress / preludeEnd);
  const storyProgress = clamp((progress - preludeEnd) / (1 - preludeEnd));
  const growth = smoothstep(storyProgress / 0.31);
  const edgeFormation = smoothstep((formation - 0.34) / 0.66);
  const revealedNodes = treeNodes.length;
  const revealedEdges = progress < preludeEnd
    ? Math.floor(graphLinks.length * edgeFormation)
    : graphLinks.length;

  treeNodes.forEach((node) => {
    node.position.lerpVectors(node.userData.scatterPosition, node.userData.treePosition, formation);
  });
  updateGraphGeometry(THREE);

  treeEdges?.geometry.setDrawRange(0, revealedEdges * 2);
  treeEdgeGlow?.geometry.setDrawRange(0, revealedEdges * 2);
  if (treeBranches) treeBranches.count = Math.min(revealedEdges, graphLinks.length);

  const functionArrival = smoothstep((storyProgress - 0.4) / 0.15);
  const reportArrival = smoothstep((storyProgress - 0.72) / 0.17);
  const functionDeparture = 1 - smoothstep((storyProgress - 0.61) / 0.1);
  const searchHighlight = smoothstep((searchSceneProgress - 0.43) / 0.13)
    * (1 - smoothstep((searchSceneProgress - 0.8) / 0.18));
  const mergeCreate = smoothstep((mergeSceneProgress - 0.04) / 0.2);
  const mergeTravel = smoothstep((mergeSceneProgress - 0.28) / 0.44);
  const mergeSettle = smoothstep((mergeSceneProgress - 0.7) / 0.17);
  const mergeFocus = mergeCreate * (1 - smoothstep((mergeSceneProgress - 0.9) / 0.09));

  if (treeEdges) treeEdges.material.opacity = edgeFormation * (0.58 - reportArrival * 0.576) * (1 - searchHighlight * 0.72) * (1 - mergeFocus * 0.58);
  if (treeEdgeGlow) treeEdgeGlow.material.opacity = edgeFormation * (0.12 - reportArrival * 0.118) * (1 - searchHighlight * 0.72) * (1 - mergeFocus * 0.58);
  if (treeBranches) treeBranches.material.opacity = edgeFormation * (0.34 - reportArrival * 0.336) * (1 - searchHighlight * 0.72) * (1 - mergeFocus * 0.58);
  if (activeRouteBranches) activeRouteBranches.material.opacity = reportArrival * 0.96;

  treeNodes.forEach((node, index) => {
    node.visible = index < revealedNodes;
    if (!node.visible) return;
    const introduction = progress < preludeEnd
      ? 0.58 + formation * 0.42
      : 1;
    const routeActive = activeRouteNodeOrders.has(node.userData.order);
    const isSearchTarget = node === searchTargetNode;
    const isMergeParent = node === mergeParentNode;
    const pulse = 1 + reportArrival * (routeActive
      ? 0.14 + Math.sin(progress * 42 + node.userData.phase) * 0.1
      : 0) + searchHighlight * (isSearchTarget
      ? 0.95 + Math.sin(searchSceneProgress * 36) * 0.12
      : 0) + mergeFocus * (isMergeParent
      ? 0.42 + Math.sin(mergeSceneProgress * 32) * 0.08
      : 0);
    node.scale.setScalar(node.userData.baseScale * introduction * pulse);

    let color = 0x1677ff;
    if (node.userData.level === 0) color = 0x0b63ce;
    else if (node.userData.channel === 0 && functionArrival > 0.05) color = 0x2994ff;
    if (reportArrival > 0.01) color = routeActive
      ? (node.userData.level === 0 ? 0x084f9f : 0x0b6edc)
      : 0x9bb2c9;
    if (searchHighlight > 0.01) color = isSearchTarget ? 0x006cff : 0x9db4ca;
    if (mergeFocus > 0.01) color = isMergeParent ? 0x0879ea : 0x9fb6cb;
    node.material.color.setHex(color);
    node.material.opacity = node.userData.level === 0
      ? 0
      : routeActive ? 0.98 : (0.98 - reportArrival * 0.91)
        * (isSearchTarget ? 1 : 1 - searchHighlight * 0.82)
        * (isMergeParent ? 1 : 1 - mergeFocus * 0.68);
    if (node.userData.halo) {
      node.userData.halo.material.color.setHex(color);
      const haloOpacity = node.userData.level === 0 ? 0.24 : 0.13;
      node.userData.halo.material.opacity = node.userData.level === 0
        ? 0
        : haloOpacity * (routeActive ? 1 : 1 - reportArrival * 0.95) * (isMergeParent ? 1 : 1 - mergeFocus * 0.7);
    }
    if (node.userData.searchHalo) {
      node.userData.searchHalo.material.opacity = searchHighlight * (0.2 + Math.sin(searchSceneProgress * 28) * 0.08);
      node.userData.searchHalo.scale.setScalar(1 + searchHighlight * 0.65);
    }
  });

  if (rootPreview) {
    const introduction = smoothstep((formation - 0.7) / 0.3);
    const pulse = 1 + reportArrival * (0.035 + Math.sin(progress * 42) * 0.018);
    rootPreview.glow.position.copy(rootPreview.root.position).add(rootPreview.offsets.glow);
    rootPreview.frame.position.copy(rootPreview.root.position).add(rootPreview.offsets.frame);
    rootPreview.screenshot.position.copy(rootPreview.root.position).add(rootPreview.offsets.screenshot);
    rootPreview.label.position.copy(rootPreview.root.position).add(rootPreview.offsets.label);
    rootPreview.glow.visible = introduction > 0;
    rootPreview.frame.visible = introduction > 0;
    rootPreview.screenshot.visible = introduction > 0;
    rootPreview.label.visible = introduction > 0;
    rootPreview.glow.scale.set(1.56 * introduction * pulse, 3.04 * introduction * pulse, 1);
    rootPreview.frame.scale.set(1.38 * introduction * pulse, 2.8 * introduction * pulse, 1);
    rootPreview.screenshot.scale.set(1.24 * introduction * pulse, 2.62 * introduction * pulse, 1);
    rootPreview.label.scale.set(1.08 * introduction, 0.3 * introduction, 1);
    rootPreview.glow.material.opacity = 0.18 + reportArrival * 0.14;
    rootPreview.screenshot.material.opacity = 1 - searchHighlight * 0.76;
    rootPreview.label.material.opacity = 1 - searchHighlight * 0.76;
    rootPreview.frame.material.opacity = 0.96 - searchHighlight * 0.76;
    rootPreview.glow.material.opacity *= 1 - searchHighlight * 0.72;
    rootPreview.screenshot.material.opacity *= 1 - mergeFocus * 0.62;
    rootPreview.label.material.opacity *= 1 - mergeFocus * 0.62;
    rootPreview.frame.material.opacity *= 1 - mergeFocus * 0.62;
    rootPreview.glow.material.opacity *= 1 - mergeFocus * 0.62;
    rootPreview.frame.material.color.setHex(reportArrival > 0.01 ? 0x075fc7 : 0x0b63ce);
  }

  if (mergeOrphanNode && mergePathCurve) {
    mergeOrphanNode.visible = mergeCreate > 0.01;
    mergeOrphanNode.position.copy(mergePathCurve.getPoint(mergeTravel));
    const mergePulse = 1 + Math.sin(mergeSceneProgress * 38) * 0.12 * (1 - mergeSettle);
    mergeOrphanNode.scale.setScalar((0.72 + mergeCreate * 0.48 - mergeSettle * 0.48) * mergePulse);
    mergeOrphanNode.material.opacity = mergeCreate * (1 - reportArrival * 0.88);
    mergeOrphanNode.material.color.setHex(mergeSettle > 0.5 ? 0x0b6edc : 0x1687ff);
    mergeOrphanHalo.material.opacity = mergeCreate * (0.2 + Math.sin(mergeSceneProgress * 30) * 0.06) * (1 - mergeSettle);
    mergeOrbitRings.forEach((ring, index) => {
      ring.material.opacity = mergeCreate * (1 - mergeSettle) * (index === 0 ? 0.72 : 0.42);
      ring.rotation.z = mergeSceneProgress * (index === 0 ? 9 : -7) + index;
      ring.scale.setScalar(1 + Math.sin(mergeSceneProgress * 24 + index) * 0.1);
    });
    mergePathLine.material.opacity = mergeCreate * (1 - mergeSettle) * 0.56;
    mergePathGlow.material.opacity = mergeCreate * (1 - mergeSettle) * (0.12 + Math.sin(mergeSceneProgress * 42) * 0.06);
    mergeFinalLine.material.opacity = mergeSettle * (0.68 - reportArrival * 0.64);
    const impactOpacity = smoothstep((mergeSettle - 0.04) / 0.22)
      * (1 - smoothstep((mergeSettle - 0.54) / 0.42));
    mergeImpactRing.material.opacity = impactOpacity * 0.84;
    mergeImpactRing.scale.setScalar(0.6 + mergeSettle * 5.2);
    mergeImpactRing.rotation.z = mergeSceneProgress * 7;

    mergeTrailParticles.forEach(({ particle, delay, phase }) => {
      const trailProgress = clamp(mergeTravel - delay);
      const active = mergeCreate > 0.01 && mergeTravel > delay && mergeSettle < 0.96;
      particle.visible = active;
      if (!active) return;
      particle.position.copy(mergePathCurve.getPoint(trailProgress));
      particle.material.opacity = (0.28 + Math.sin(mergeSceneProgress * 48 + phase) * 0.2) * (1 - mergeSettle);
      particle.scale.setScalar(0.65 + Math.sin(mergeSceneProgress * 40 + phase) * 0.24);
    });
  }

  injectionBeams.forEach((beam) => {
    const base = functionArrival * functionDeparture;
    const local = clamp((base - beam.phase) / 0.52);
    beam.line.geometry.setDrawRange(0, Math.floor(beam.pointCount * local));
    beam.line.material.opacity = local > 0 ? 0.18 + local * 0.48 : 0;
    beam.orb.material.opacity = local > 0 && local < 0.94 ? 0.9 : 0;
    beam.orb.visible = local > 0;
    beam.orb.position.copy(beam.curve.getPoint(smoothstep(local)));
    beam.arrow.material.opacity = smoothstep((local - 0.72) / 0.22) * 0.94;
    beam.arrow.scale.setScalar(0.72 + local * 0.34);
  });

  movingSignals.forEach((item, index) => {
    const active = reportArrival > index / movingSignals.length * 0.34;
    item.signal.visible = active;
    if (!active) return;
    item.signal.material.opacity = 0.56 + Math.sin(progress * 90 + index) * 0.38;
  });

  baseWorldRotationY = formation * 0.16 + storyProgress * Math.PI * 2.25;
  baseWorldRotationX = -0.12 + Math.sin(storyProgress * Math.PI * 2) * 0.12;
  world.position.y = -0.2 + Math.sin(progress * Math.PI) * -0.3;
  camera.position.z = cameraBaseZ + (1 - formation) * 1.8 - growth * 0.6 + reportArrival * 0.8;
  camera.position.y = 0.5 + Math.sin(progress * Math.PI * 3) * 0.55;
  camera.lookAt(new THREE.Vector3(0, 0.1, 0));
}

function renderFrame(time = 0) {
  if (!renderer || !scene || !camera || !world) return;
  pointerX += (targetPointerX - pointerX) * 0.035;
  pointerY += (targetPointerY - pointerY) * 0.035;
  if (!dragging.value) {
    manualRotationY += rotationVelocityY;
    manualRotationX = clamp(manualRotationX + rotationVelocityX, -0.72, 0.72);
    rotationVelocityY *= 0.93;
    rotationVelocityX *= 0.9;
    if (Math.abs(rotationVelocityY) < 0.00002) rotationVelocityY = 0;
    if (Math.abs(rotationVelocityX) < 0.00002) rotationVelocityX = 0;
  }
  camera.position.x = pointerX * 0.48;
  camera.rotation.z = -pointerX * 0.008;
  world.rotation.y = baseWorldRotationY + manualRotationY;
  world.rotation.x = baseWorldRotationX + manualRotationX;
  world.rotation.z = pointerY * 0.025;
  starField.rotation.y = time * 0.000012;

  const reportArrival = smoothstep((currentProgress - 0.68) / 0.18);
  movingSignals.forEach((item, index) => {
    if (!item.signal.visible) return;
    const travel = (time * 0.00022 * (1 + reportArrival) + item.phase) % 1;
    item.signal.position.lerpVectors(item.from, item.to, travel);
    item.signal.scale.setScalar(0.7 + Math.sin(time * 0.008 + index) * 0.25);
  });

  renderer.render(scene, camera);
  animationFrame = requestAnimationFrame(renderFrame);
}

function resizeRenderer() {
  if (!renderer || !camera || !overlayRef.value) return;
  const width = overlayRef.value.clientWidth;
  const height = overlayRef.value.clientHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / Math.max(height, 1);
  cameraBaseZ = camera.aspect < 0.7 ? 36 : camera.aspect < 1.1 ? 28 : 22.5;
  camera.updateProjectionMatrix();
  updateThreeScene(currentProgress);
}

onBeforeUnmount(() => {
  setupVersion += 1;
  destroyJourney();
  if (open.value) document.body.style.overflow = previousBodyOverflow;
});

onMounted(() => {
  openJourney();
});
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      ref="overlayRef"
      class="journey-overlay"
      :class="{
        'is-dragging': dragging,
        'search-result-active': searchResultVisible && searchDemoOpacity > 0.05,
        'merge-demo-active': mergeDemoOpacity > 0.05,
      }"
      role="dialog"
      aria-modal="true"
      aria-label="App Graph 三维项目旅程"
      tabindex="-1"
      @keydown="handleKeydown"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
      @pointercancel="handlePointerUp"
    >
      <div class="journey-progress" aria-hidden="true"><span ref="progressRef" /></div>

      <header class="journey-header">
        <div class="journey-brand">
          <span class="journey-brand-mark" aria-hidden="true">◎</span>
          <div><strong>APP GRAPH</strong><small>EVOLUTION STORY / 3D</small></div>
        </div>
        <span class="journey-counter">{{ scenes[activeScene].number }} / {{ scenes[scenes.length - 1].number }}</span>
        <div class="journey-actions">
          <button class="journey-icon-button" type="button" aria-label="重置三维树视角" title="重置视角" @click="resetTreeView">↻</button>
        </div>
      </header>

      <div class="journey-visual" aria-hidden="true">
        <canvas ref="canvasRef" />
        <div class="journey-vignette" />
        <div class="journey-axis axis-x" />
        <div class="journey-axis axis-y" />

        <div class="journey-stream stream-hdc" :class="{ visible: activeScene === 0 }">
          <span>HDC DEVICE LINK</span><strong>散点采集 → 关系拟合</strong><i /><b>URL · SCREENSHOT · WIDGET</b>
        </div>

        <div
          class="journey-search-demo"
          :class="{ visible: searchDemoOpacity > 0.01, 'result-visible': searchResultVisible }"
          :style="searchPanelStyle"
        >
          <div class="journey-search-label"><span /> URL INTELLIGENCE SEARCH</div>
          <div class="journey-search-input">
            <i aria-hidden="true" />
            <span>{{ searchQuery }}</span><b v-if="searchQuery.length < searchTargetUrl.length" />
          </div>
          <div class="journey-search-status">
            <span>{{ searchResultVisible ? 'MATCHED' : 'NORMALIZING URL' }}</span>
            <strong>{{ searchResultVisible ? '96.8%' : '...' }}</strong>
          </div>
          <div class="journey-search-result">
            <div class="journey-search-shot">
              <img :src="douyinHomeScreenshot" alt="搜索结果页面截图" />
              <span>AI</span>
            </div>
            <div class="journey-search-analysis">
              <em>命中节点 / 搜索结果页</em>
              <h3>性能关键词搜索结果</h3>
              <p>大模型判断该页面属于搜索功能域。页面包含搜索框、结果列表与筛选入口，可从首页搜索控件抵达。</p>
              <dl>
                <div><dt>PAGE URL</dt><dd>aweme://search/result</dd></div>
                <div><dt>IMAGE</dt><dd>1080 × 2400 · JPEG</dd></div>
                <div><dt>ACTION</dt><dd>pageNaviAction</dd></div>
              </dl>
            </div>
          </div>
        </div>

        <div
          class="journey-merge-demo"
          :class="{ visible: mergeDemoOpacity > 0.01, complete: mergeStage === 3 }"
          :style="{ opacity: mergeDemoOpacity }"
        >
          <div class="journey-merge-heading">
            <span>NODE INTAKE PIPELINE</span><strong>#N-308</strong>
          </div>
          <div class="journey-merge-url">aweme://poi/detail/98231</div>
          <div class="journey-merge-steps">
            <div class="journey-merge-rail"><i :style="{ height: `${Math.min(mergeStage / 3, 1) * 100}%` }" /></div>
            <div class="journey-merge-step" :class="{ active: mergeStage === 0, done: mergeStage > 0 }">
              <b>01</b><span><strong>创建游离节点</strong><small>写入 URL 与原始截图证据</small></span><em>{{ mergeStage > 0 ? 'CREATED' : 'CREATING' }}</em>
            </div>
            <div class="journey-merge-step" :class="{ active: mergeStage === 1, done: mergeStage > 1 }">
              <b>02</b><span><strong>AI 补全页面信息</strong><small>摘要 · embedding_text · actions</small></span><em>{{ mergeStage > 1 ? 'READY' : mergeStage === 1 ? 'ANALYZING' : 'WAIT' }}</em>
            </div>
            <div class="journey-merge-step" :class="{ active: mergeStage === 2, done: mergeStage > 2 }">
              <b>03</b><span><strong>确认候选父节点</strong><small>语义匹配并校验新边无环</small></span><em>{{ mergeStage > 2 ? 'VERIFIED' : mergeStage === 2 ? 'MATCHING' : 'WAIT' }}</em>
            </div>
            <div class="journey-merge-step" :class="{ active: mergeStage === 3, done: mergeStage === 3 }">
              <b>04</b><span><strong>并入应用主树</strong><small>生成边关系并刷新图谱</small></span><em>{{ mergeStage === 3 ? 'MERGED' : 'WAIT' }}</em>
            </div>
          </div>
        </div>

        <svg
          class="journey-scenario-arrows"
          :class="{ visible: activeScene === 4 && mergeDemoOpacity < 0.05 }"
          viewBox="0 0 1000 1000"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <marker id="scenario-arrow-login" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 Z" fill="#0b63ce" />
            </marker>
            <marker id="scenario-arrow-register" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 Z" fill="#1677ff" />
            </marker>
            <marker id="scenario-arrow-like" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 Z" fill="#47a5ff" />
            </marker>
            <marker id="scenario-arrow-favorite" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 Z" fill="#78baff" />
            </marker>
          </defs>
          <g class="scenario-arrow arrow-login">
            <path d="M245 282 C310 282 355 382 445 418" marker-end="url(#scenario-arrow-login)" />
            <circle cx="445" cy="418" r="8" />
          </g>
          <g class="scenario-arrow arrow-register">
            <path d="M245 364 C325 364 342 498 392 554" marker-end="url(#scenario-arrow-register)" />
            <circle cx="392" cy="554" r="8" />
          </g>
          <g class="scenario-arrow arrow-like">
            <path d="M245 446 C322 446 370 616 452 652" marker-end="url(#scenario-arrow-like)" />
            <circle cx="452" cy="652" r="8" />
          </g>
          <g class="scenario-arrow arrow-favorite">
            <path d="M245 528 C338 528 418 718 505 788" marker-end="url(#scenario-arrow-favorite)" />
            <circle cx="505" cy="788" r="8" />
          </g>
        </svg>

        <div
          class="journey-scenario-list"
          :class="{ visible: activeScene === 4 && mergeDemoOpacity < 0.05 }"
        >
          <div class="journey-scenario-heading">
            <span>SCENARIO FUNCTION LIST</span>
            <strong>4 / 4 MATCHED</strong>
          </div>
          <div class="journey-scenario-items">
            <div
              v-for="(item, index) in scenarioFunctions"
              :key="item.code"
              class="journey-scenario-item"
              :style="{ '--scenario-color': item.color, '--scenario-delay': `${index * 90}ms` }"
            >
              <i>{{ String(index + 1).padStart(2, '0') }}</i>
              <span>
                <strong>{{ item.name }}</strong>
                <small>{{ item.code }} · {{ item.target }}</small>
              </span>
              <em>MATCHED</em>
              <b aria-hidden="true">→</b>
            </div>
          </div>
        </div>
        <div class="journey-stream stream-cases" :class="{ visible: activeScene >= 5 }">
          <span>TEST CASE ENGINE</span><strong>路径 × 动作</strong><i />
        </div>
        <div class="journey-stream stream-report" :class="{ visible: activeScene >= 6 }">
          <span>LIVE SIGNAL</span><strong>性能数据回流</strong><i />
        </div>

        <div v-if="loading" class="journey-loading">
          <span />
          <small>构建三维图谱</small>
        </div>
      </div>

      <nav class="journey-nav" aria-label="项目旅程章节">
        <button
          v-for="(item, index) in scenes"
          :key="item.id"
          type="button"
          :class="{ active: activeScene === index, passed: activeScene > index }"
          :aria-label="`前往第 ${item.number} 章：${item.title}`"
          @click="scrollToScene(index)"
        >
          <span>{{ item.number }}</span><i />
        </button>
      </nav>

      <div ref="scrollRef" class="journey-scroll">
        <main class="journey-story">
          <section
            v-for="sceneItem in scenes"
            :key="sceneItem.id"
            class="journey-section"
            :class="`section-${sceneItem.id}`"
            :data-side="sceneItem.side"
          >
            <article class="journey-copy" :class="`copy-${sceneItem.side}`">
              <span class="journey-number">{{ sceneItem.number }}</span>
              <em>{{ sceneItem.kicker }}</em>
              <h2>{{ sceneItem.title }}</h2>
              <p>{{ sceneItem.text }}</p>
              <div class="journey-tags">
                <span v-for="tag in sceneItem.tags" :key="tag">{{ tag }}</span>
              </div>
              <div class="journey-metric">
                <strong>{{ sceneItem.metric }}</strong>
                <span>{{ sceneItem.metricLabel }}</span>
              </div>
            </article>
          </section>
        </main>
      </div>

      <div class="journey-scroll-hint" :class="{ hidden: activeScene > 0 }">
        <span aria-hidden="true">↓</span>
        <span>滚轮推进 · 空白处拖拽旋转</span>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.journey-overlay { position: fixed; z-index: 10000; inset: 0; overflow: hidden; background: #f4f8fd; color: #173a5e; font-family: Inter,"PingFang SC","Microsoft YaHei",sans-serif; outline: none; user-select: none; }
.journey-overlay.is-dragging { cursor: grabbing; }
.journey-progress { position: absolute; z-index: 20; top: 0; right: 0; left: 0; height: 3px; background: #dce9f6; }
.journey-progress span { display: block; width: 100%; height: 100%; background: #1677ff; box-shadow: 0 0 16px rgba(22,119,255,.32); transform: scaleX(0); }
.journey-header { position: absolute; z-index: 15; top: 0; right: 0; left: 0; display: grid; height: 74px; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 0 34px; border-bottom: 1px solid rgba(126,164,202,.28); background: rgba(255,255,255,.84); box-shadow: 0 8px 30px rgba(48,93,138,.06); backdrop-filter: blur(18px); }
.journey-brand { display: flex; align-items: center; gap: 11px; }
.journey-brand-mark { display: grid; width: 36px; height: 36px; place-items: center; border: 1px solid #9bc8f5; background: #fff; color: #1677ff; box-shadow: inset 0 0 18px rgba(22,119,255,.06),0 6px 18px rgba(22,119,255,.08); }
.journey-brand div { display: grid; gap: 3px; }
.journey-brand strong { font-size: 12px; letter-spacing: .15em; }
.journey-brand small { color: #7893ad; font-size: 8px; letter-spacing: .22em; }
.journey-counter { color: #547596; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 11px; letter-spacing: .16em; }
.journey-actions { display: flex; justify-self: end; gap: 8px; }
.journey-icon-button { display: grid; width: 34px; height: 34px; padding: 0; place-items: center; border: 1px solid #c7daed; background: #fff; color: #3e668c; box-shadow: 0 3px 10px rgba(43,92,139,.06); cursor: pointer; font-size: 18px; line-height: 1; }
.journey-icon-button:hover { border-color: #1677ff; background: #eaf4ff; color: #0b63ce; }
.journey-icon-button:focus-visible { outline: 2px solid #1677ff; outline-offset: 2px; }
.journey-visual { position: absolute; z-index: 1; inset: 0; overflow: hidden; pointer-events: none; }
.journey-visual canvas { display: block; width: 100%; height: 100%; }
.journey-vignette { position: absolute; inset: 0; border: 1px solid rgba(111,158,205,.16); box-shadow: inset 0 0 160px rgba(90,151,211,.07); }
.journey-axis { position: absolute; opacity: .35; background: #b3d1ec; }
.axis-x { top: 50%; right: 3%; left: 3%; height: 1px; }
.axis-y { top: 9%; bottom: 7%; left: 50%; width: 1px; }
.journey-stream { position: absolute; display: grid; min-width: 146px; gap: 4px; opacity: 0; transition: opacity .5s ease,transform .7s ease; }
.journey-stream span { font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 9px; letter-spacing: .16em; }
.journey-stream strong { color: #173a5e; font-size: 12px; font-weight: 650; }
.journey-stream b { color: #6b89a5; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 8px; font-weight: 600; letter-spacing: .12em; }
.journey-stream i { width: 100%; height: 1px; box-shadow: 0 0 12px currentColor; }
.journey-stream.visible { opacity: .9; transform: translateX(0); }
.stream-hdc { top: 22%; right: 5%; color: #0b63ce; text-align: right; transform: translateX(60px); }
.stream-hdc i { margin-left: auto; background: linear-gradient(90deg,transparent,#1677ff); animation: hdc-scan 1.6s ease-in-out infinite; }
.stream-cases { right: 4%; bottom: 31%; color: #4d91d7; text-align: right; transform: translateX(60px); }
.stream-report { bottom: 9%; left: 50%; color: #0b63ce; text-align: center; transform: translate(-50%,30px); }
.stream-report.visible { transform: translate(-50%,0); }
.journey-scenario-list { position: absolute; top: 20%; left: 4%; width: min(264px,25vw); border-top: 2px solid #1677ff; background: rgba(248,252,255,.9); box-shadow: 0 18px 42px rgba(38,91,143,.13); opacity: 0; visibility: hidden; transform: translateX(-34px); transition: opacity .45s ease,transform .65s cubic-bezier(.2,.8,.2,1),visibility .2s; backdrop-filter: blur(14px); }
.journey-scenario-list.visible { opacity: 1; visibility: visible; transform: translateX(0); }
.journey-scenario-arrows { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; opacity: 0; visibility: hidden; transition: opacity .35s ease .2s,visibility .2s; }
.journey-scenario-arrows.visible { opacity: .92; visibility: visible; }
.scenario-arrow path { fill: none; stroke-width: 1.35; stroke-dasharray: 9 7; vector-effect: non-scaling-stroke; animation: scenario-flow 1.5s linear infinite; }
.scenario-arrow circle { fill: rgba(255,255,255,.82); stroke-width: 1.4; vector-effect: non-scaling-stroke; transform-box: fill-box; transform-origin: center; animation: scenario-target 1.7s ease-in-out infinite; }
.arrow-login path,.arrow-login circle { stroke: #0b63ce; }
.arrow-register path,.arrow-register circle { stroke: #1677ff; }
.arrow-like path,.arrow-like circle { stroke: #47a5ff; }
.arrow-favorite path,.arrow-favorite circle { stroke: #78baff; }
.journey-scenario-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 11px 12px 9px; border-right: 1px solid #d4e4f3; border-bottom: 1px solid #d4e4f3; border-left: 1px solid #d4e4f3; color: #647f99; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 7px; font-weight: 700; letter-spacing: .13em; }
.journey-scenario-heading strong { color: #1677ff; font-size: 7px; white-space: nowrap; }
.journey-scenario-items { border-right: 1px solid #d4e4f3; border-left: 1px solid #d4e4f3; }
.journey-scenario-item { position: relative; display: grid; min-height: 58px; grid-template-columns: 28px minmax(0,1fr) auto 14px; align-items: center; gap: 8px; padding: 7px 9px; border-bottom: 1px solid #dce9f5; background: rgba(255,255,255,.76); opacity: 0; transform: translateX(-16px); transition: opacity .38s ease var(--scenario-delay),transform .5s cubic-bezier(.2,.8,.2,1) var(--scenario-delay),background .25s ease; }
.journey-scenario-list.visible .journey-scenario-item { opacity: 1; transform: translateX(0); }
.journey-scenario-item::before { position: absolute; top: 0; bottom: 0; left: 0; width: 2px; background: var(--scenario-color); box-shadow: 0 0 12px var(--scenario-color); content: ''; }
.journey-scenario-item:hover { background: #eef7ff; }
.journey-scenario-item > i { display: grid; width: 25px; height: 25px; place-items: center; border: 1px solid color-mix(in srgb,var(--scenario-color) 50%,white); background: #fff; color: var(--scenario-color); font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 8px; font-style: normal; font-weight: 800; }
.journey-scenario-item > span { display: grid; min-width: 0; gap: 3px; }
.journey-scenario-item > span strong { color: #234c73; font-size: 12px; }
.journey-scenario-item > span small { overflow: hidden; color: #7590a9; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 7px; text-overflow: ellipsis; white-space: nowrap; }
.journey-scenario-item > em { color: var(--scenario-color); font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 6px; font-style: normal; font-weight: 800; letter-spacing: .08em; }
.journey-scenario-item > b { color: var(--scenario-color); font-size: 15px; font-weight: 500; animation: scenario-arrow 1.4s ease-in-out infinite; }
@keyframes scenario-arrow { 50% { opacity: .48; transform: translateX(4px); } }
@keyframes scenario-flow { to { stroke-dashoffset: -32; } }
@keyframes scenario-target { 50% { opacity: .42; transform: scale(1.65); } }
.journey-search-demo { position: absolute; top: 17%; left: 5.5%; width: min(370px,34vw); opacity: 0; transition: visibility .2s; visibility: hidden; transform-origin: 100% 50%; }
.journey-search-demo.visible { visibility: visible; }
.journey-search-label { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; color: #537493; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 8px; font-weight: 700; letter-spacing: .16em; }
.journey-search-label span { width: 6px; height: 6px; border: 1px solid #1677ff; background: #eaf4ff; box-shadow: 0 0 10px rgba(22,119,255,.42); transform: rotate(45deg); }
.journey-search-input { display: flex; height: 42px; align-items: center; gap: 11px; padding: 0 13px; border: 1px solid #9bc8f5; background: rgba(255,255,255,.94); box-shadow: 0 10px 28px rgba(50,103,154,.12),inset 0 0 0 1px rgba(255,255,255,.9); }
.journey-search-input i { position: relative; width: 13px; height: 13px; flex: 0 0 13px; border: 1.5px solid #1677ff; border-radius: 50%; }
.journey-search-input i::after { position: absolute; right: -5px; bottom: -3px; width: 6px; height: 1.5px; background: #1677ff; content: ''; transform: rotate(45deg); transform-origin: left center; }
.journey-search-input span { overflow: hidden; color: #234a70; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.journey-search-input b { width: 1px; height: 16px; flex: 0 0 1px; background: #1677ff; animation: search-caret .72s steps(1) infinite; }
.journey-search-status { display: flex; align-items: center; justify-content: space-between; padding: 7px 2px 12px; color: #7993ac; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 8px; letter-spacing: .12em; }
.journey-search-status strong { color: #1677ff; font-size: 9px; }
.journey-search-result { display: grid; grid-template-columns: 96px 1fr; gap: 14px; padding: 12px; border: 1px solid rgba(139,184,226,.72); background: rgba(255,255,255,.94); box-shadow: 0 20px 46px rgba(52,105,157,.16); opacity: 0; transform: translateY(22px) scale(.94); transition: opacity .42s ease,transform .55s cubic-bezier(.2,.8,.2,1); }
.result-visible .journey-search-result { opacity: 1; transform: translateY(0) scale(1); }
.journey-search-shot { position: relative; overflow: hidden; aspect-ratio: 9/18.5; border: 2px solid #d4e4f3; background: #dfeaf5; box-shadow: 0 8px 20px rgba(39,91,141,.14); }
.journey-search-shot img { width: 100%; height: 100%; object-fit: cover; }
.journey-search-shot span { position: absolute; top: 5px; right: 5px; display: grid; width: 22px; height: 16px; place-items: center; background: #1677ff; color: #fff; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 7px; font-weight: 800; }
.journey-search-analysis { display: flex; min-width: 0; flex-direction: column; gap: 7px; }
.journey-search-analysis em { color: #1677ff; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 8px; font-style: normal; font-weight: 700; letter-spacing: .1em; }
.journey-search-analysis h3 { margin: 0; color: #173f65; font-size: 15px; letter-spacing: 0; }
.journey-search-analysis p { margin: 0; color: #567590; font-size: 10px; line-height: 1.65; }
.journey-search-analysis dl { display: grid; gap: 5px; margin: auto 0 0; }
.journey-search-analysis dl div { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: 8px; border-top: 1px solid #e1ebf5; padding-top: 4px; }
.journey-search-analysis dt { color: #8aa0b5; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 7px; }
.journey-search-analysis dd { overflow: hidden; margin: 0; color: #365e83; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 7px; text-overflow: ellipsis; white-space: nowrap; }
.journey-merge-demo { position: absolute; top: 17%; right: 5.5%; overflow: hidden; width: min(390px,35vw); padding: 14px; border: 1px solid rgba(139,184,226,.78); background: rgba(255,255,255,.94); box-shadow: 0 22px 52px rgba(45,99,151,.16); opacity: 0; visibility: hidden; transform: translateX(34px); transition: transform .45s ease,visibility .2s; }
.journey-merge-demo::before { position: absolute; z-index: 0; top: -35%; bottom: -35%; left: -20%; width: 18%; background: linear-gradient(90deg,transparent,rgba(90,179,255,.2),transparent); content: ''; pointer-events: none; transform: skewX(-16deg); animation: merge-panel-scan 2.1s ease-in-out infinite; }
.journey-merge-demo > * { position: relative; z-index: 1; }
.journey-merge-demo.visible { visibility: visible; transform: translateX(0); }
.journey-merge-demo.complete { border-color: #6baff2; box-shadow: 0 22px 52px rgba(22,119,255,.2),inset 0 0 0 1px rgba(22,119,255,.08); }
.journey-merge-heading { display: flex; align-items: center; justify-content: space-between; color: #6584a1; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 8px; font-weight: 700; letter-spacing: .14em; }
.journey-merge-heading strong { color: #1677ff; font-size: 9px; }
.journey-merge-url { overflow: hidden; margin-top: 10px; padding: 9px 10px; border: 1px solid #c5dbef; background: #f5faff; color: #315d84; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; box-shadow: inset 3px 0 0 #1677ff; }
.journey-merge-steps { position: relative; display: grid; gap: 3px; margin-top: 11px; padding-left: 23px; }
.journey-merge-rail { position: absolute; top: 12px; bottom: 12px; left: 8px; width: 1px; background: #d5e5f3; }
.journey-merge-rail i { position: absolute; top: 0; left: 0; width: 1px; background: #1677ff; box-shadow: 0 0 8px rgba(22,119,255,.5); transition: height .38s ease; }
.journey-merge-step { position: relative; display: grid; min-height: 47px; grid-template-columns: 25px minmax(0,1fr) auto; align-items: center; gap: 8px; padding: 6px 7px; border: 1px solid transparent; opacity: .46; transition: opacity .25s ease,border-color .25s ease,background .25s ease; }
.journey-merge-step::before { position: absolute; top: 50%; left: -19px; width: 7px; height: 7px; border: 1px solid #a8bfd5; background: #fff; content: ''; transform: translateY(-50%) rotate(45deg); }
.journey-merge-step.active { border-color: #9fc9ee; background: #f5faff; box-shadow: inset 0 0 18px rgba(22,119,255,.07),0 0 18px rgba(22,119,255,.06); opacity: 1; }
.journey-merge-step.done { opacity: .82; }
.journey-merge-step.active::before,.journey-merge-step.done::before { border-color: #1677ff; background: #1677ff; box-shadow: 0 0 10px rgba(22,119,255,.42); }
.journey-merge-step > b { color: #9bb0c4; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 9px; }
.journey-merge-step.active > b,.journey-merge-step.done > b { color: #1677ff; }
.journey-merge-step > span { display: grid; min-width: 0; gap: 3px; }
.journey-merge-step > span strong { color: #315a80; font-size: 10px; font-weight: 700; }
.journey-merge-step > span small { overflow: hidden; color: #8299ae; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
.journey-merge-step > em { color: #8ba1b5; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 7px; font-style: normal; font-weight: 700; letter-spacing: .06em; }
.journey-merge-step.active > em,.journey-merge-step.done > em { color: #1677ff; }
@keyframes merge-panel-scan { 0% { left: -22%; opacity: 0; } 18% { opacity: 1; } 68%,100% { left: 112%; opacity: 0; } }
.journey-loading { position: absolute; top: 50%; left: 50%; display: grid; gap: 11px; place-items: center; transform: translate(-50%,-50%); }
.journey-loading span { width: 34px; height: 34px; border: 1px solid #c5d9ec; border-top-color: #1677ff; border-radius: 50%; animation: journey-spin .8s linear infinite; }
.journey-loading small { color: #6785a2; font-size: 9px; letter-spacing: .16em; }
@keyframes journey-spin { to { transform: rotate(360deg); } }
@keyframes hdc-scan { 0%,100% { width: 38%; opacity: .35; } 50% { width: 100%; opacity: 1; } }
@keyframes search-caret { 50% { opacity: 0; } }
.journey-scroll { position: absolute; z-index: 4; inset: 0; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; scrollbar-width: none; }
.journey-scroll::-webkit-scrollbar { display: none; }
.journey-story { position: relative; }
.journey-section { position: relative; display: flex; min-height: 112svh; align-items: center; padding: 102px max(7vw,76px) 64px; }
.journey-section[data-side="right"] { justify-content: flex-end; }
.journey-copy { position: relative; display: grid; width: min(540px,42vw); gap: 17px; text-shadow: 0 2px 18px rgba(255,255,255,.96); }
.journey-number { position: absolute; z-index: -1; top: -100px; left: -28px; color: rgba(22,119,255,.08); font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 132px; font-weight: 800; line-height: 1; }
.copy-right .journey-number { right: -12px; left: auto; }
.journey-copy em { color: #1677ff; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 10px; font-style: normal; font-weight: 700; letter-spacing: .2em; }
.section-scene-function .journey-copy em { color: #1677ff; }
.section-prelude .journey-copy em { color: #0b63ce; }
.section-node-merge .journey-copy em { color: #1687ff; }
.section-test-case .journey-copy em { color: #4d91d7; }
.section-observability .journey-copy em { color: #0b63ce; }
.journey-copy h2 { max-width: 540px; margin: 0; color: #12385f; font-size: clamp(34px,4vw,58px); font-weight: 670; line-height: 1.12; letter-spacing: 0; text-wrap: balance; }
.journey-copy p { max-width: 510px; margin: 0; color: #4f6f8e; font-size: 14px; line-height: 1.9; }
.journey-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.journey-tags span { padding: 6px 9px; border: 1px solid #bfd5e9; border-radius: 3px; background: rgba(255,255,255,.78); color: #315c82; font-size: 10px; font-weight: 650; box-shadow: 0 3px 12px rgba(45,92,138,.04); backdrop-filter: blur(8px); }
.journey-metric { display: grid; width: max-content; gap: 3px; margin-top: 18px; padding-left: 15px; border-left: 2px solid #1677ff; }
.journey-metric strong { color: #173a5e; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 24px; letter-spacing: .03em; }
.journey-metric span { color: #65839f; font-size: 10px; }
.section-scene-function .journey-metric { border-color: #1677ff; }
.section-prelude .journey-metric { border-color: #0b63ce; }
.section-node-merge .journey-metric { border-color: #1687ff; }
.section-test-case .journey-metric { border-color: #4d91d7; }
.section-observability .journey-metric { border-color: #0b63ce; }
.journey-nav { position: absolute; z-index: 12; top: 50%; left: 24px; display: grid; gap: 0; transform: translateY(-50%); }
.journey-nav button { display: flex; width: 35px; height: 34px; align-items: center; gap: 8px; padding: 0; border: 0; background: transparent; color: #7891a9; cursor: pointer; }
.journey-nav button span { width: 20px; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 9px; text-align: right; }
.journey-nav button i { width: 4px; height: 4px; border: 1px solid #7891a9; background: #f4f8fd; transform: rotate(45deg); transition: all .25s ease; }
.journey-nav button.passed { color: #5f82a4; }
.journey-nav button.passed i { border-color: #4d91d7; background: #4d91d7; }
.journey-nav button.active { color: #0b63ce; }
.journey-nav button.active i { width: 8px; height: 8px; border-color: #1677ff; background: #1677ff; box-shadow: 0 0 12px rgba(22,119,255,.45); }
.journey-nav button:focus-visible { outline: 1px solid #1677ff; outline-offset: 3px; }
.journey-scroll-hint { position: absolute; z-index: 13; bottom: 24px; left: 50%; display: flex; align-items: center; gap: 8px; color: #6685a3; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 9px; letter-spacing: .18em; transform: translateX(-50%); transition: opacity .35s ease; animation: journey-hint 1.8s ease-in-out infinite; }
.journey-scroll-hint.hidden { opacity: 0; }
@keyframes journey-hint { 50% { transform: translate(-50%,8px); } }
@media (max-width: 900px) {
  .journey-header { height: 66px; padding: 0 18px; }
  .journey-counter { display: none; }
  .journey-section { min-height: 108svh; padding: 88px 36px 70px; }
  .journey-copy { width: min(500px,56vw); }
  .journey-copy h2 { font-size: clamp(31px,5.5vw,48px); }
  .journey-nav { left: 10px; }
  .journey-search-demo { top: 14%; left: 4%; width: min(330px,42vw); }
  .search-result-active .section-exploration .journey-copy { opacity: 0 !important; visibility: hidden; }
  .journey-merge-demo { top: 14%; right: 4%; width: min(350px,44vw); }
  .merge-demo-active .section-node-merge .journey-copy { opacity: 0 !important; visibility: hidden; }
  .journey-scenario-list { top: 17%; left: 3%; width: min(244px,30vw); }
  .stream-cases { right: 3%; }
}
@media (max-width: 640px) {
  .journey-brand small { display: none; }
  .journey-section,.journey-section[data-side="right"] { min-height: 108svh; align-items: flex-end; justify-content: flex-start; padding: 82px 22px 84px; }
  .journey-copy { width: 100%; gap: 11px; padding: 18px 16px; border-top: 1px solid rgba(92,151,210,.3); background: rgba(255,255,255,.84); box-shadow: 0 -10px 34px rgba(66,112,157,.08); backdrop-filter: blur(16px); }
  .journey-copy h2 { font-size: 29px; }
  .journey-copy p { font-size: 12px; line-height: 1.7; }
  .journey-number { top: -50px; left: 4px; font-size: 74px; }
  .copy-right .journey-number { right: 4px; }
  .journey-tags { display: none; }
  .journey-metric { margin-top: 6px; }
  .journey-metric strong { font-size: 18px; }
  .journey-nav { top: auto; right: 16px; bottom: 22px; left: 16px; display: flex; justify-content: flex-end; transform: none; }
  .journey-nav button { width: 27px; justify-content: center; }
  .journey-nav button span { display: none; }
  .journey-stream { display: none; }
  .journey-scenario-arrows { display: none; }
  .journey-scenario-list { top: 84px; right: 16px; left: 16px; width: auto; }
  .journey-scenario-heading { padding: 8px 10px; }
  .journey-scenario-item { min-height: 44px; grid-template-columns: 24px minmax(0,1fr) auto 12px; padding: 4px 8px; }
  .journey-scenario-item > i { width: 21px; height: 21px; }
  .journey-scenario-list.visible ~ .journey-loading { display: none; }
  .section-scene-function .journey-copy { margin-top: 292px; }
  .journey-search-demo { top: 88px; right: 16px; left: 16px; width: auto; }
  .journey-merge-demo { top: 88px; right: 16px; left: 16px; width: auto; padding: 10px; }
  .journey-merge-step { min-height: 43px; grid-template-columns: 23px minmax(0,1fr) auto; padding: 4px 5px; }
  .journey-search-result { grid-template-columns: 70px 1fr; gap: 10px; padding: 9px; }
  .journey-search-analysis p { display: none; }
  .journey-search-analysis h3 { font-size: 13px; }
  .journey-scroll-hint { bottom: 24px; left: 22px; transform: none; }
  @keyframes journey-hint { 50% { transform: translateY(8px); } }
}
@media (prefers-reduced-motion: reduce) {
  .journey-loading span,.journey-scroll-hint { animation: none; }
  .journey-scroll { scroll-behavior: auto; }
  .journey-stream,.journey-scenario-list,.journey-scenario-item,.journey-scenario-arrows { transition: none; }
  .journey-scenario-item > b,.scenario-arrow path,.scenario-arrow circle { animation: none; }
}
</style>
