import streamlit as st
import streamlit.components.v1 as components

# 1. 스트림릿 페이지 기본 설정
st.set_page_config(
    page_title="Streamlit 3D FPS Game",
    page_icon="🎮",
    layout="wide"
)

# 사이드바 및 UI 타이틀
st.title("🎮 Streamlit 3D FPS Game")
st.sidebar.header("게임 조작법")
st.sidebar.markdown("""
- **이동**: `W`, `A`, `S`, `D`
- **조준/시점**: 마우스 이동
- **사격**: 마우스 좌클릭 (데미지: 10)
- **목표**: 체력 100인 AI 적을 10번 맞춰 처치
""")

# 2. HTML / JavaScript / Three.js 3D 게임 임베딩 코드
game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      overflow: hidden;
      font-family: sans-serif;
      background-color: #000;
    }
    /* Crosshair */
    #crosshair {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 10px;
      height: 10px;
      margin-top: -5px;
      margin-left: -5px;
      border-radius: 50%;
      background-color: red;
      pointer-events: none;
      z-index: 10;
    }
    /* UI (적 체력) */
    #ui {
      position: absolute;
      top: 20px;
      left: 20px;
      color: white;
      font-size: 20px;
      background: rgba(0, 0, 0, 0.6);
      padding: 10px 20px;
      border-radius: 5px;
      pointer-events: none;
      z-index: 10;
    }
    /* 시작 화면 안내 */
    #instructions {
      position: absolute;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.7);
      color: white;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      font-size: 24px;
      cursor: pointer;
      z-index: 20;
    }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/PointerLockControls.js"></script>
</head>
<body>

  <div id="crosshair"></div>
  <div id="ui">적 체력: <span id="hp">100</span> / 100</div>
  <div id="instructions">
    <p>⚡ 이 화면을 클릭하여 게임을 시작하세요 ⚡</p>
    <p style="font-size: 16px; color: #ccc;">(ESC 키를 누르면 마우스 커서가 해제됩니다)</p>
  </div>

  <script>
    // 1. Scene / Camera / Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87ceeb); // 하늘색

    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    // Light
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(10, 20, 10);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x404040));

    // Floor
    const floorGeometry = new THREE.PlaneGeometry(100, 100);
    const floorMaterial = new THREE.MeshBasicMaterial({ color: 0x228b22, side: THREE.DoubleSide });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = Math.PI / 2;
    scene.add(floor);

    // 2. AI 적 생성 (체력 100)
    let enemyHP = 100;
    const enemyGeometry = new THREE.BoxGeometry(2, 4, 2);
    const enemyMaterial = new THREE.MeshLambertMaterial({ color: 0xff0000 });
    const enemy = new THREE.Mesh(enemyGeometry, enemyMaterial);
    enemy.position.set(0, 2, -15);
    scene.add(enemy);

    // 3. 컨트롤 및 시점 (PointerLock)
    const controls = new THREE.PointerLockControls(camera, document.body);
    const instructions = document.getElementById('instructions');

    instructions.addEventListener('click', () => {
      controls.lock();
    });

    controls.addEventListener('lock', () => {
      instructions.style.display = 'none';
    });

    controls.addEventListener('unlock', () => {
      instructions.style.display = 'flex';
    });

    // WASD 키 상태
    const moveState = { forward: false, backward: false, left: false, right: false };

    document.addEventListener('keydown', (e) => {
      switch (e.code) {
        case 'KeyW': moveState.forward = true; break;
        case 'KeyS': moveState.backward = true; break;
        case 'KeyA': moveState.left = true; break;
        case 'KeyD': moveState.right = true; break;
      }
    });

    document.addEventListener('keyup', (e) => {
      switch (e.code) {
        case 'KeyW': moveState.forward = false; break;
        case 'KeyS': moveState.backward = false; break;
        case 'KeyA': moveState.left = false; break;
        case 'KeyD': moveState.right = false; break;
      }
    });

    // 4. 사격 (Raycaster)
    const raycaster = new THREE.Raycaster();

    document.addEventListener('mousedown', (e) => {
      if (!controls.isLocked || e.button !== 0) return;

      raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
      const intersects = raycaster.intersectObject(enemy);

      if (intersects.length > 0 && enemyHP > 0) {
        enemyHP -= 10;
        document.getElementById('hp').innerText = enemyHP;

        // 피격 시 잠시 하얗게 깜빡임
        enemy.material.color.setHex(0xffffff);
        setTimeout(() => enemy.material.color.setHex(0xff0000), 100);

        if (enemyHP <= 0) {
          scene.remove(enemy);
          document.getElementById('ui').innerText = "🎉 적 처치 완료!";
        }
      }
    });

    camera.position.y = 2;

    // 5. Game Loop
    const clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const moveSpeed = 10.0 * delta;

      if (controls.isLocked) {
        if (moveState.forward) controls.moveForward(moveSpeed);
        if (moveState.backward) controls.moveForward(-moveSpeed);
        if (moveState.left) controls.moveRight(-moveSpeed);
        if (moveState.right) controls.moveRight(moveSpeed);
      }

      // 간단한 AI (플레이어 추적)
      if (enemyHP > 0) {
        enemy.lookAt(camera.position.x, enemy.position.y, camera.position.z);
        const distance = enemy.position.distanceTo(camera.position);
        if (distance > 3) {
          enemy.translateZ(1.5 * delta);
        }
      }

      renderer.render(scene, camera);
    }

    animate();

    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  </script>
</body>
</html>
"""

# 3. Streamlit 화면에 렌더링 (높이 700px 설정)
components.html(game_html, height=700)
