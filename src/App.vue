<script setup>
import douyinHomeScreenshot from './assets/douyin-home-root.jpg';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

gsap.registerPlugin(ScrollTrigger);

const open = ref(false);
const loading = ref(false);
const dragging = ref(false);
const activeScene = ref(0);
const overlayRef = ref(null);
const scrollRef = ref(null);
const canvasRef = ref(null);
const progressRef = ref(null);

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
let graphLinks = [];
let activeRouteNodeOrders = new Set();
let activeRouteEdgeIndexes = new Set();
let movingSignals = [];
let injectionBeams = [];
let starField = null;
let threeApi = null;

const scenes = [
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
    kicker: 'DEVICE EXPLORATION',
    title: '脚本向前走，图谱向外生长',
    text: 'HDC 脚本在真实设备点击、滑动与长按。AI 读取截图、URL 和页面结构，去重动态内容，并把每一次新发现接回已有分支。滚动此刻，树冠正在展开。',
    tags: ['HDC Script', 'AI Vision', '增量遍历'],
    metric: '4 ACTIONS',
    metricLabel: '弹层 · 状态 · 外部 · 跳转',
    side: 'right',
  },
  {
    id: 'function-tree',
    number: '03',
    kicker: 'FUNCTION TREE INJECTION',
    title: '官方功能树，从左侧注入',
    text: '厂商提供的 Function Tree 不再是一份孤立清单。900 个功能点经过索引、语义匹配与批量复核，沿着左侧光束进入页面节点，让“发现了什么”和“应该覆盖什么”第一次对齐。',
    tags: ['功能目录', '语义匹配', '覆盖缺口'],
    metric: '900',
    metricLabel: '厂商功能点可定位',
    side: 'left',
  },
  {
    id: 'test-case',
    number: '04',
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
    number: '05',
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
    number: '06',
    kicker: 'CONTINUOUS APP INTELLIGENCE',
    title: '它不再只是一张图，而是持续生长的应用认知',
    text: '游离页面、人工证据、AI 推断、Function Tree、测试用例与性能结果共享同一棵树。每一次采集都补充认知，每一次复核都提高可信度，每一次执行都让下一次探索更聪明。',
    tags: ['持续覆盖', '人机共审', '图谱治理'],
    metric: '8 STAGES',
    metricLabel: '从图谱原型走向工程平台',
    side: 'right',
  },
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
  treeBranches.instanceMatrix.setUsage(THREE.StaticDrawUsage);
  const routeLinks = graphLinks.filter((_, index) => activeRouteEdgeIndexes.has(index));
  const routeBranchGeometry = new THREE.CylinderGeometry(0.036, 0.062, 1, 8, 1, true);
  const routeBranchMaterial = new THREE.MeshBasicMaterial({
    color: 0x075fc7,
    transparent: true,
    opacity: 0,
    blending: THREE.NormalBlending,
    depthWrite: false,
  });
  activeRouteBranches = new THREE.InstancedMesh(routeBranchGeometry, routeBranchMaterial, routeLinks.length);
  activeRouteBranches.instanceMatrix.setUsage(THREE.StaticDrawUsage);
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
  routeLinks.forEach((link, index) => {
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
  rootPreview = { root, glow, frame, screenshot, label };
}

function createInjectionBeams(THREE, side, color) {
  const direction = side === 'left' ? -1 : 1;
  const targetPool = treeNodes.filter((node) => node.userData.level >= 2);

  for (let index = 0; index < 9; index += 1) {
    const target = targetPool[(index * 11 + (side === 'left' ? 2 : 7)) % targetPool.length];
    const start = new THREE.Vector3(direction * (11.5 + index * 0.16), -4.4 + index * 1.05, -1.5 + (index % 3));
    const control = new THREE.Vector3(direction * (7.5 + (index % 3)), target.position.y + Math.sin(index) * 2.3, 3.2);
    const curve = new THREE.QuadraticBezierCurve3(start, control, target.position.clone());
    const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(42));
    const material = new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: 0,
      blending: THREE.NormalBlending,
      depthWrite: false,
    });
    const line = new THREE.Line(geometry, material);
    const orb = new THREE.Mesh(
      new THREE.SphereGeometry(0.105, 8, 8),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, blending: THREE.NormalBlending, depthWrite: false }),
    );
    orb.position.copy(start);
    world.add(line, orb);
    injectionBeams.push({ side, curve, line, orb, target, phase: index * 0.055 });
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
  const growth = smoothstep(progress / 0.31);
  const revealedNodes = Math.max(1, Math.floor(treeNodes.length * (0.06 + growth * 0.94)));
  const revealedEdges = Math.max(0, revealedNodes - 1);

  treeEdges?.geometry.setDrawRange(0, revealedEdges * 2);
  treeEdgeGlow?.geometry.setDrawRange(0, revealedEdges * 2);
  if (treeBranches) treeBranches.count = Math.min(revealedEdges, graphLinks.length);

  const functionArrival = smoothstep((progress - 0.32) / 0.17);
  const reportArrival = smoothstep((progress - 0.68) / 0.18);
  const functionDeparture = 1 - smoothstep((progress - 0.56) / 0.1);

  if (treeEdges) treeEdges.material.opacity = 0.58 - reportArrival * 0.576;
  if (treeEdgeGlow) treeEdgeGlow.material.opacity = 0.12 - reportArrival * 0.118;
  if (treeBranches) treeBranches.material.opacity = 0.34 - reportArrival * 0.336;
  if (activeRouteBranches) activeRouteBranches.material.opacity = reportArrival * 0.96;

  treeNodes.forEach((node, index) => {
    node.visible = index < revealedNodes;
    if (!node.visible) return;
    const introduction = clamp((revealedNodes - index) / 10);
    const routeActive = activeRouteNodeOrders.has(node.userData.order);
    const pulse = 1 + reportArrival * (routeActive
      ? 0.14 + Math.sin(progress * 42 + node.userData.phase) * 0.1
      : 0);
    node.scale.setScalar(node.userData.baseScale * introduction * pulse);

    let color = 0x1677ff;
    if (node.userData.level === 0) color = 0x0b63ce;
    else if (node.userData.channel === 0 && functionArrival > 0.05) color = 0x2994ff;
    if (reportArrival > 0.01) color = routeActive
      ? (node.userData.level === 0 ? 0x084f9f : 0x0b6edc)
      : 0x9bb2c9;
    node.material.color.setHex(color);
    node.material.opacity = node.userData.level === 0
      ? 0
      : routeActive ? 0.98 : 0.98 - reportArrival * 0.91;
    if (node.userData.halo) {
      node.userData.halo.material.color.setHex(color);
      const haloOpacity = node.userData.level === 0 ? 0.24 : 0.13;
      node.userData.halo.material.opacity = node.userData.level === 0
        ? 0
        : haloOpacity * (routeActive ? 1 : 1 - reportArrival * 0.95);
    }
  });

  if (rootPreview) {
    const introduction = clamp(revealedNodes / 4);
    const pulse = 1 + reportArrival * (0.035 + Math.sin(progress * 42) * 0.018);
    rootPreview.glow.visible = introduction > 0;
    rootPreview.frame.visible = introduction > 0;
    rootPreview.screenshot.visible = introduction > 0;
    rootPreview.label.visible = introduction > 0;
    rootPreview.glow.scale.set(1.56 * introduction * pulse, 3.04 * introduction * pulse, 1);
    rootPreview.frame.scale.set(1.38 * introduction * pulse, 2.8 * introduction * pulse, 1);
    rootPreview.screenshot.scale.set(1.24 * introduction * pulse, 2.62 * introduction * pulse, 1);
    rootPreview.label.scale.set(1.08 * introduction, 0.3 * introduction, 1);
    rootPreview.glow.material.opacity = 0.18 + reportArrival * 0.14;
    rootPreview.frame.material.color.setHex(reportArrival > 0.01 ? 0x075fc7 : 0x0b63ce);
  }

  injectionBeams.forEach((beam) => {
    const base = functionArrival * functionDeparture;
    const local = clamp((base - beam.phase) / 0.62);
    beam.line.material.opacity = local > 0 ? 0.1 + local * 0.34 : 0;
    beam.orb.material.opacity = local > 0 && local < 1 ? 1 : local === 1 ? 0.32 : 0;
    beam.orb.visible = local > 0;
    beam.orb.position.copy(beam.curve.getPoint(smoothstep(local)));
  });

  movingSignals.forEach((item, index) => {
    const active = reportArrival > index / movingSignals.length * 0.34;
    item.signal.visible = active;
    if (!active) return;
    item.signal.material.opacity = 0.56 + Math.sin(progress * 90 + index) * 0.38;
  });

  baseWorldRotationY = progress * Math.PI * 2.25;
  baseWorldRotationX = -0.12 + Math.sin(progress * Math.PI * 2) * 0.12;
  world.position.y = -0.2 + Math.sin(progress * Math.PI) * -0.3;
  camera.position.z = cameraBaseZ - growth * 0.6 + reportArrival * 0.8;
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
      :class="{ 'is-dragging': dragging }"
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
        <span class="journey-counter">{{ scenes[activeScene].number }} / {{ String(scenes.length).padStart(2, '0') }}</span>
        <div class="journey-actions">
          <button class="journey-icon-button" type="button" aria-label="重置三维树视角" title="重置视角" @click="resetTreeView">↻</button>
        </div>
      </header>

      <div class="journey-visual" aria-hidden="true">
        <canvas ref="canvasRef" />
        <div class="journey-vignette" />
        <div class="journey-axis axis-x" />
        <div class="journey-axis axis-y" />

        <div class="journey-stream stream-function" :class="{ visible: activeScene >= 2 }">
          <span>FUNCTION TREE</span><strong>900 功能点</strong><i />
        </div>
        <div class="journey-stream stream-cases" :class="{ visible: activeScene >= 3 }">
          <span>TEST CASE ENGINE</span><strong>路径 × 动作</strong><i />
        </div>
        <div class="journey-stream stream-report" :class="{ visible: activeScene >= 4 }">
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
.journey-stream i { width: 100%; height: 1px; box-shadow: 0 0 12px currentColor; }
.journey-stream.visible { opacity: .9; transform: translateX(0); }
.stream-function { top: 28%; left: 4%; color: #1677ff; transform: translateX(-60px); }
.stream-cases { right: 4%; bottom: 31%; color: #4d91d7; text-align: right; transform: translateX(60px); }
.stream-report { bottom: 9%; left: 50%; color: #0b63ce; text-align: center; transform: translate(-50%,30px); }
.stream-report.visible { transform: translate(-50%,0); }
.journey-loading { position: absolute; top: 50%; left: 50%; display: grid; gap: 11px; place-items: center; transform: translate(-50%,-50%); }
.journey-loading span { width: 34px; height: 34px; border: 1px solid #c5d9ec; border-top-color: #1677ff; border-radius: 50%; animation: journey-spin .8s linear infinite; }
.journey-loading small { color: #6785a2; font-size: 9px; letter-spacing: .16em; }
@keyframes journey-spin { to { transform: rotate(360deg); } }
.journey-scroll { position: absolute; z-index: 4; inset: 0; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; scrollbar-width: none; }
.journey-scroll::-webkit-scrollbar { display: none; }
.journey-story { position: relative; }
.journey-section { position: relative; display: flex; min-height: 112svh; align-items: center; padding: 102px max(7vw,76px) 64px; }
.journey-section[data-side="right"] { justify-content: flex-end; }
.journey-copy { position: relative; display: grid; width: min(540px,42vw); gap: 17px; text-shadow: 0 2px 18px rgba(255,255,255,.96); }
.journey-number { position: absolute; z-index: -1; top: -100px; left: -28px; color: rgba(22,119,255,.08); font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 132px; font-weight: 800; line-height: 1; }
.copy-right .journey-number { right: -12px; left: auto; }
.journey-copy em { color: #1677ff; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 10px; font-style: normal; font-weight: 700; letter-spacing: .2em; }
.section-function-tree .journey-copy em { color: #1677ff; }
.section-test-case .journey-copy em { color: #4d91d7; }
.section-observability .journey-copy em { color: #0b63ce; }
.journey-copy h2 { max-width: 540px; margin: 0; color: #12385f; font-size: clamp(34px,4vw,58px); font-weight: 670; line-height: 1.12; letter-spacing: 0; text-wrap: balance; }
.journey-copy p { max-width: 510px; margin: 0; color: #4f6f8e; font-size: 14px; line-height: 1.9; }
.journey-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.journey-tags span { padding: 6px 9px; border: 1px solid #bfd5e9; border-radius: 3px; background: rgba(255,255,255,.78); color: #315c82; font-size: 10px; font-weight: 650; box-shadow: 0 3px 12px rgba(45,92,138,.04); backdrop-filter: blur(8px); }
.journey-metric { display: grid; width: max-content; gap: 3px; margin-top: 18px; padding-left: 15px; border-left: 2px solid #1677ff; }
.journey-metric strong { color: #173a5e; font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-size: 24px; letter-spacing: .03em; }
.journey-metric span { color: #65839f; font-size: 10px; }
.section-function-tree .journey-metric { border-color: #1677ff; }
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
  .stream-function { left: 3%; }
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
  .journey-scroll-hint { bottom: 24px; left: 22px; transform: none; }
  @keyframes journey-hint { 50% { transform: translateY(8px); } }
}
@media (prefers-reduced-motion: reduce) {
  .journey-loading span,.journey-scroll-hint { animation: none; }
  .journey-scroll { scroll-behavior: auto; }
  .journey-stream { transition: none; }
}
</style>
