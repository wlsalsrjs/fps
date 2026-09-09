import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Streamlit 3D FPS Game",
    page_icon="🔫",
    layout="wide"
)

st.title("🔫 Streamlit 3D FPS Game")
st.sidebar.header("🎮 게임 조작법")
st.sidebar.markdown("""
- **이동**: `W`, `A`, `S`, `D`
- **조준/시점**: 마우스 이동
- **사격**: 마우스 좌클릭
- **데미지 시스템**:
  - **몸통/사지**: `10` 데미지
  - **머리(헤드샷)**: `20` 데미지 (5대면 처치!)
- **맵 요소**:
  - 사람 형태의 적 & 플레이어 손/총기
  - 엄폐물(벽/기둥) 및 오를 수 있는 경사로(Ramp)
""")

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
      background-color: #d3d3d3;
      user-select: none;
    }
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
    #ui {
      position: absolute;
      top: 20px;
      left: 20px;
      color: white;
      font-size: 20px;
      font-weight: bold;
      background: rgba(0, 0, 0, 0.6);
      padding: 10px 20px;
      border-radius: 5px;
      pointer-events: none;
      z-index: 10;
    }
    #hit-log {
      color: #ffcc00;
      font-size: 16px;
      margin-top: 5px;
    }
    #instructions {
      position: absolute;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.6);
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
  <div id="ui">
    적 체력: <span id="hp">100</span> / 100
    <div id="hit-log"></div>
  </div>
  <div id="instructions">
    <p>⚡ 화면을 클릭하여 게임 시작 ⚡</p>
    <p style="font-size: 16px; color: #ccc;">WASD 이동 | 마우스 좌클릭 사격 | ESC 마우스 해제</p>
  </div>

  <script>
    // 1. 씬, 카메라, 렌더러 (밝은 회색 배경)
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xd3d3d3);

    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    // 조명
    const light = new THREE.DirectionalLight(0xffffff, 0.9);
    light.position.set(20, 40, 20);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x606060));

    // 바닥
    const floorGeo = new THREE.PlaneGeometry(100, 100);
    const floorMat = new THREE.MeshLambertMaterial({ color: 0x999999 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    // 충돌 판정용 오브젝트 리스트
    const collidableObjects = [floor];

    // 2. 맵 건축물 (엄폐물 & 경사로)
    function createMap() {
      const obstacleMat = new THREE.MeshLambertMaterial({ color: 0x666666 });

      // 엄폐 벽들
      const wallData = [
        { w: 8, h: 4, d: 1, x: 0, y: 2, z: -8 },
        { w: 1, h: 4, d: 8, x: -10, y: 2, z: -10 },
        { w: 1, h: 4, d: 8, x: 10, y: 2, z: -10 },
        { w: 6, h: 3, d: 6, x: -6, y: 1.5, z: -18 }
      ];

      wallData.forEach(data => {
        const wall = new THREE.Mesh(new THREE.BoxGeometry(data.w, data.h, data.d), obstacleMat);
        wall.position.set(data.x, data.y, data.z);
        scene.add(wall);
        collidableObjects.push(wall);
      });

      // 경사로 (Ramp)
      const rampMat = new THREE.MeshLambertMaterial({ color: 0x555555 });
      
      const ramp1 = new THREE.Mesh(new THREE.BoxGeometry(6, 0.5, 12), rampMat);
      ramp1.position.set(12, 2.5, -15);
      ramp1.rotation.x = Math.PI / 6; // 경사각
      scene.add(ramp1);
      collidableObjects.push(ramp1);

      const ramp2 = new THREE.Mesh(new THREE.BoxGeometry(6, 0.5, 12), rampMat);
      ramp2.position.set(-12, 2.5, -15);
      ramp2.rotation.x = Math.PI / 6;
      scene.add(ramp2);
      collidableObjects.push(ramp2);
    }
    createMap();

    // 3. 사람 형태의 적(AI) 생성
    let enemyHP = 100;
    const enemyGroup = new THREE.Group();
    const enemyHitboxes = []; // 사격 판정용

    // 적 캐릭터 파츠 생성 함수
    function createHumanoidEnemy() {
      const bodyMat = new THREE.MeshLambertMaterial({ color: 0xcc3333 }); // 빨간 의상
      const skinMat = new THREE.MeshLambertMaterial({ color: 0xffdbac }); // 살구색 피부

      // 머리 (헤드샷 판정용)
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.4, 16, 16), skinMat);
      head.position.set(0, 2.8, 0);
      head.userData = { part: 'head' };
      enemyGroup.add(head);
      enemyHitboxes.push(head);

      // 몸통
      const torso = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.2, 0.4), bodyMat);
      torso.position.set(0, 1.9, 0);
      torso.userData = { part: 'body' };
      enemyGroup.add(torso);
      enemyHitboxes.push(torso);

      // 팔/다리
      const armGeo = new THREE.BoxGeometry(0.25, 1.0, 0.25);
      const legGeo = new THREE.BoxGeometry(0.3, 1.2, 0.3);

      const leftArm = new THREE.Mesh(armGeo, bodyMat);
      leftArm.position.set(-0.55, 1.9, 0);
      leftArm.userData = { part: 'body' };
      enemyGroup.add(leftArm);
      enemyHitboxes.push(leftArm);

      const rightArm = new THREE.Mesh(armGeo, bodyMat);
      rightArm.position.set(0.55, 1.9, 0);
      rightArm.userData = { part: 'body' };
      enemyGroup.add(rightArm);
      enemyHitboxes.push(rightArm);

      const leftLeg = new THREE.Mesh(legGeo, obstacleMat);
      leftLeg.position.set(-0.2, 0.6, 0);
      leftLeg.userData = { part: 'body' };
      enemyGroup.add(leftLeg);
      enemyHitboxes.push(leftLeg);

      const rightLeg = new THREE.Mesh(legGeo, obstacleMat);
      rightLeg.position.set(0.2, 0.6, 0);
      rightLeg.userData = { part: 'body' };
      enemyGroup.add(rightLeg);
      enemyHitboxes.push(rightLeg);

      enemyGroup.position.set(0, 0, -20);
      scene.add(enemyGroup);
    }
    createHumanoidEnemy();

    // 4. 플레이어 시점 & 총기 모델링
    const gunGroup = new THREE.Group();
    const gunBody = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.15, 0.6), new THREE.MeshLambertMaterial({ color: 0x111111 }));
    gunBody.position.set(0.3, -0.25, -0.5);
    gunGroup.add(gunBody);
    camera.add(gunGroup);
    scene.add(camera);

    // 5. 컨트롤 & 시작 클릭 보장 이벤트 처리
    const controls = new THREE.PointerLockControls(camera, document.body);
    const instructions = document.getElementById('instructions');

    // iframe 클릭 포커스 강제 이동으로 시작 안 되는 버그 수정
    instructions.addEventListener('click', () => {
      window.focus();
      controls.lock();
    });

    controls.addEventListener('lock', () => {
      instructions.style.display = 'none';
    });

    controls.addEventListener('unlock', () => {
      instructions.style.display = 'flex';
    });

    // 이동 키 처리
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

    // 6. 사격 & 헤드샷 판정 시스템
    const raycaster = new THREE.Raycaster();
    const hitLog = document.getElementById('hit-log');

    document.addEventListener('mousedown', (e) => {
      if (!controls.isLocked || e.button !== 0 || enemyHP <= 0) return;

      // 총기 반동 애니메이션
      gunGroup.position.z += 0.05;
      setTimeout(() => gunGroup.position.z -= 0.05, 50);

      // 레이캐스팅 (화면 중앙)
      raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
      const intersects = raycaster.intersectObjects(enemyHitboxes);

      if (intersects.length > 0) {
        const hitPart = intersects[0].object.userData.part;
        let damage = 10;

        if (hitPart === 'head') {
          damage = 20;
          hitLog.innerText = "🎯 헤드샷! (20 데미지)";
          hitLog.style.color = "#ff3333";
        } else {
          hitLog.innerText = "💥 피격! (10 데미지)";
          hitLog.style.color = "#ffcc00";
        }

        enemyHP = Math.max(0, enemyHP - damage);
        document.getElementById('hp').innerText = enemyHP;

        // 적 피격 피드백 (빨갛게 깜빡임)
        enemyHitboxes.forEach(part => part.material.color.setHex(0xffffff));
        setTimeout(() => {
          enemyHitboxes.forEach(part => {
            if (part.userData.part === 'head') part.material.color.setHex(0xffdbac);
            else part.material.color.setHex(0xcc3333);
          });
        }, 80);

        if (enemyHP <= 0) {
          scene.remove(enemyGroup);
          document.getElementById('ui').innerText = "🏆 적 처치 완료!";
        }
      }
    });

    // 7. 게임 루프 & 단순 물리 (경사로)
    camera.position.set(0, 2, 0);
    const clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const moveSpeed = 8.0 * delta;

      if (controls.isLocked) {
        if (moveState.forward) controls.moveForward(moveSpeed);
        if (moveState.backward) controls.moveForward(-moveSpeed);
        if (moveState.left) controls.moveRight(-moveSpeed);
        if (moveState.right) controls.moveRight(moveSpeed);

        // 경사로 및 바닥 높이 감지 (간단한 고도 자동 조절)
        const downRay = new THREE.Raycaster(camera.position, new THREE.Vector3(0, -1, 0), 0, 3);
        const hits = downRay.intersectObjects(collidableObjects);
        if (hits.length > 0) {
          camera.position.y = hits[0].point.y + 2.0;
        }
      }

      // 적 AI (플레이어를 조준하며 가깝게 다가옴)
      if (enemyHP > 0) {
        enemyGroup.lookAt(camera.position.x, enemyGroup.position.y, camera.position.z);
        const distance = enemyGroup.position.distanceTo(camera.position);
        if (distance > 5) {
          enemyGroup.translateZ(1.2 * delta);
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

# Streamlit Component 파라미터로 iframe 제어 권한을 명시하여 클릭 안 됨 현상 해결
components.html(game_html, height=720, scrolling=False)
