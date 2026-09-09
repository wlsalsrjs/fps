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
- **시작**: 별도 클릭 없이 **마우스 커서를 게임 화면에 올리고 움직이면 바로 플레이 가능**합니다.
- **이동**: `W`, `A`, `S`, `D`
- **시점 전환**: 마우스 이동
- **사격**: 마우스 좌클릭
- **데미지 판정**:
  - **머리(헤드샷)**: `20` 데미지
  - **몸통 / 다리**: `10` 데미지
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
    /* 십자선 (크로스헤어) */
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
    /* UI (적 체력 및 상태) */
    #ui {
      position: absolute;
      top: 20px;
      left: 20px;
      color: white;
      font-size: 20px;
      font-weight: bold;
      background: rgba(0, 0, 0, 0.6);
      padding: 12px 24px;
      border-radius: 8px;
      pointer-events: none;
      z-index: 10;
    }
    #hit-log {
      color: #ffcc00;
      font-size: 16px;
      margin-top: 6px;
    }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

  <div id="crosshair"></div>
  <div id="ui">
    적 체력: <span id="hp">100</span> / 100
    <div id="hit-log">마우스로 조준하고 클릭하여 사격하세요!</div>
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
    const floorGeo = new THREE.PlaneGeometry(120, 120);
    const floorMat = new THREE.MeshLambertMaterial({ color: 0x888888 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    const collidableObjects = [floor];

    // 2. 풍부한 엄폐물 및 경사로 맵 생성
    function createMap() {
      const obstacleMat = new THREE.MeshLambertMaterial({ color: 0x555555 });
      const pillarMat = new THREE.MeshLambertMaterial({ color: 0x444444 });
      const rampMat = new THREE.MeshLambertMaterial({ color: 0x666666 });

      // [엄폐물 구조물 데이터 목록]
      const structures = [
        // 중앙 엄폐 벽 단지
        { w: 6, h: 3, d: 1, x: 0, y: 1.5, z: -8 },
        { w: 1, h: 3, d: 6, x: -4, y: 1.5, z: -12 },
        { w: 1, h: 3, d: 6, x: 4, y: 1.5, z: -12 },
        { w: 8, h: 2, d: 1, x: 0, y: 1, z: -16 },

        // 좌측 및 우측 엄폐 기둥/벽들
        { w: 2, h: 5, d: 2, x: -10, y: 2.5, z: -6 },
        { w: 2, h: 5, d: 2, x: 10, y: 2.5, z: -6 },
        { w: 10, h: 3, d: 1, x: -14, y: 1.5, z: -15 },
        { w: 10, h: 3, d: 1, x: 14, y: 1.5, z: -15 },
        { w: 2, h: 4, d: 2, x: -8, y: 2, z: -22 },
        { w: 2, h: 4, d: 2, x: 8, y: 2, z: -22 },

        // 후방 엄폐박스들
        { w: 3, h: 1.5, d: 3, x: -3, y: 0.75, z: -25 },
        { w: 3, h: 1.5, d: 3, x: 3, y: 0.75, z: -25 }
      ];

      structures.forEach(s => {
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(s.w, s.h, s.d), obstacleMat);
        mesh.position.set(s.x, s.y, s.z);
        scene.add(mesh);
        collidableObjects.push(mesh);
      });

      // 경사로 (Ramp) 2개
      const ramp1 = new THREE.Mesh(new THREE.BoxGeometry(5, 0.5, 10), rampMat);
      ramp1.position.set(12, 2.2, -22);
      ramp1.rotation.x = Math.PI / 6;
      scene.add(ramp1);
      collidableObjects.push(ramp1);

      const ramp2 = new THREE.Mesh(new THREE.BoxGeometry(5, 0.5, 10), rampMat);
      ramp2.position.set(-12, 2.2, -22);
      ramp2.rotation.x = Math.PI / 6;
      scene.add(ramp2);
      collidableObjects.push(ramp2);
    }
    createMap();

    // 3. 사람 형태의 적(AI) 생성
    let enemyHP = 100;
    const enemyGroup = new THREE.Group();
    const enemyHitboxes = [];

    function createHumanoidEnemy() {
      const bodyMat = new THREE.MeshLambertMaterial({ color: 0xcc3333 }); // 빨간 옷
      const skinMat = new THREE.MeshLambertMaterial({ color: 0xffdbac }); // 살구색 피부
      const pantsMat = new THREE.MeshLambertMaterial({ color: 0x222222 });

      // 머리 (헤드샷 20 데미지)
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.4, 16, 16), skinMat);
      head.position.set(0, 2.8, 0);
      head.userData = { part: 'head' };
      enemyGroup.add(head);
      enemyHitboxes.push(head);

      // 몸통 (10 데미지)
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

      const leftLeg = new THREE.Mesh(legGeo, pantsMat);
      leftLeg.position.set(-0.2, 0.6, 0);
      leftLeg.userData = { part: 'body' };
      enemyGroup.add(leftLeg);
      enemyHitboxes.push(leftLeg);

      const rightLeg = new THREE.Mesh(legGeo, pantsMat);
      rightLeg.position.set(0.2, 0.6, 0);
      rightLeg.userData = { part: 'body' };
      enemyGroup.add(rightLeg);
      enemyHitboxes.push(rightLeg);

      enemyGroup.position.set(0, 0, -28);
      scene.add(enemyGroup);
    }
    createHumanoidEnemy();

    // 4. 플레이어 시점 & 마우스 회전 제어 (클릭 방식 제외)
    camera.position.set(0, 2, 0);

    let pitch = 0; // 상하 회전
    let yaw = 0;   // 좌우 회전

    // 마우스 이동 시 시점 회전
    window.addEventListener('mousemove', (e) => {
      const sensitivity = 0.002;
      yaw -= e.movementX * sensitivity;
      pitch -= e.movementY * sensitivity;

      // 상하 시점 제한 (-80도 ~ 80도)
      pitch = Math.max(-Math.PI / 2.2, Math.min(Math.PI / 2.2, pitch));

      const euler = new THREE.Euler(0, 0, 0, 'YXZ');
      euler.x = pitch;
      euler.y = yaw;
      camera.quaternion.setFromEuler(euler);
    });

    // 5. WASD 이동
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

    // 6. 사격 기능
    const raycaster = new THREE.Raycaster();
    const hitLog = document.getElementById('hit-log');

    window.addEventListener('mousedown', (e) => {
      if (e.button !== 0 || enemyHP <= 0) return;

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
          hitLog.innerText = "💥 몸통 피격! (10 데미지)";
          hitLog.style.color = "#ffcc00";
        }

        enemyHP = Math.max(0, enemyHP - damage);
        document.getElementById('hp').innerText = enemyHP;

        // 적 피격 피드백
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

    // 7. 메인 게임 루프
    const clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const moveSpeed = 8.0 * delta;

      // 카메라 정면 및 측면 방향 벡터 계산
      const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
      forward.y = 0;
      forward.normalize();

      const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
      right.y = 0;
      right.normalize();

      if (moveState.forward) camera.position.addScaledVector(forward, moveSpeed);
      if (moveState.backward) camera.position.addScaledVector(forward, -moveSpeed);
      if (moveState.left) camera.position.addScaledVector(right, -moveSpeed);
      if (moveState.right) camera.position.addScaledVector(right, moveSpeed);

      // 경사로 및 높이 감지
      const downRay = new THREE.Raycaster(camera.position, new THREE.Vector3(0, -1, 0), 0, 3);
      const hits = downRay.intersectObjects(collidableObjects);
      if (hits.length > 0) {
        camera.position.y = hits[0].point.y + 2.0;
      }

      // AI 추적 행동
      if (enemyHP > 0) {
        enemyGroup.lookAt(camera.position.x, enemyGroup.position.y, camera.position.z);
        const distance = enemyGroup.position.distanceTo(camera.position);
        if (distance > 5) {
          enemyGroup.translateZ(1.5 * delta);
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

components.html(game_html, height=720, scrolling=False)
