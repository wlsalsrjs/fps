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
- **마우스 고정**: 게임 화면을 한번 터치/클릭하면 즉시 마우스가 고정됩니다.
- **마우스 해제**: `ESC` 키
- **이동**: `W`, `A`, `S`, `D`
- **사격**: 마우스 좌클릭
- **데미지 판정**:
  - **머리(헤드샷)**: `20` 데미지
  - **몸통 / 다리**: `10` 데미지
- **AI 공격**: 적도 플레이어를 추적하여 총을 쏩니다.
- **물리 법칙**:
  - 벽, 엄폐물, 중앙 대형 벽은 통과가 불가능합니다.
  - 경사로나 엄폐물 위에서 발을 헛디디면 아래로 **낙하**합니다.
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
    /* 크로스헤어 (조준점) */
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
    /* 상단 UI (체력 및 상태) */
    #ui {
      position: absolute;
      top: 20px;
      left: 20px;
      color: white;
      font-size: 18px;
      font-weight: bold;
      background: rgba(0, 0, 0, 0.7);
      padding: 12px 20px;
      border-radius: 8px;
      pointer-events: none;
      z-index: 10;
    }
    #hit-log {
      color: #ffcc00;
      font-size: 14px;
      margin-top: 6px;
    }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/PointerLockControls.js"></script>
</head>
<body>

  <div id="crosshair"></div>
  <div id="ui">
    <div>나의 체력: <span id="player-hp" style="color: #00ff00;">100</span> / 100</div>
    <div>적의 체력: <span id="enemy-hp" style="color: #ff4444;">100</span> / 100</div>
    <div id="hit-log">화면을 클릭하면 시점이 고정되어 바로 시작됩니다 (ESC: 고정 해제)</div>
  </div>

  <script>
    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xd3d3d3);

    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    // Light
    const light = new THREE.DirectionalLight(0xffffff, 0.9);
    light.position.set(20, 40, 20);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x606060));

    // Floor
    const floorGeo = new THREE.PlaneGeometry(120, 120);
    const floorMat = new THREE.MeshLambertMaterial({ color: 0x888888 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    const wallObjects = [];
    const groundObjects = [floor];

    // 2. Map (중앙 벽, 엄폐물, 경사로)
    function createMap() {
      const obstacleMat = new THREE.MeshLambertMaterial({ color: 0x555555 });
      const mainWallMat = new THREE.MeshLambertMaterial({ color: 0x333333 });
      const rampMat = new THREE.MeshLambertMaterial({ color: 0x666666 });

      // 초반 가림막 벽
      const centerWall = new THREE.Mesh(new THREE.BoxGeometry(30, 8, 1), mainWallMat);
      centerWall.position.set(0, 4, -15);
      scene.add(centerWall);
      wallObjects.push(centerWall);

      // 엄폐물 배치
      const structures = [
        { w: 4, h: 3, d: 1, x: -8, y: 1.5, z: -8 },
        { w: 4, h: 3, d: 1, x: 8, y: 1.5, z: -8 },
        { w: 2, h: 5, d: 2, x: -12, y: 2.5, z: -15 },
        { w: 2, h: 5, d: 2, x: 12, y: 2.5, z: -15 },
        { w: 6, h: 2, d: 1, x: -6, y: 1, z: -22 },
        { w: 6, h: 2, d: 1, x: 6, y: 1, z: -22 },
        { w: 3, h: 1.5, d: 3, x: 0, y: 0.75, z: -5 }
      ];

      structures.forEach(s => {
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(s.w, s.h, s.d), obstacleMat);
        mesh.position.set(s.x, s.y, s.z);
        scene.add(mesh);
        wallObjects.push(mesh);
        groundObjects.push(mesh);
      });

      // 경사로
      const ramp1 = new THREE.Mesh(new THREE.BoxGeometry(5, 0.5, 10), rampMat);
      ramp1.position.set(12, 2.2, -22);
      ramp1.rotation.x = Math.PI / 6;
      scene.add(ramp1);
      groundObjects.push(ramp1);

      const ramp2 = new THREE.Mesh(new THREE.BoxGeometry(5, 0.5, 10), rampMat);
      ramp2.position.set(-12, 2.2, -22);
      ramp2.rotation.x = Math.PI / 6;
      scene.add(ramp2);
      groundObjects.push(ramp2);
    }
    createMap();

    // 3. Humanoid AI Enemy
    let enemyHP = 100;
    let playerHP = 100;
    const enemyGroup = new THREE.Group();
    const enemyHitboxes = [];

    function createHumanoidEnemy() {
      const bodyMat = new THREE.MeshLambertMaterial({ color: 0xcc3333 });
      const skinMat = new THREE.MeshLambertMaterial({ color: 0xffdbac });
      const pantsMat = new THREE.MeshLambertMaterial({ color: 0x222222 });

      // Head
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.4, 16, 16), skinMat);
      head.position.set(0, 2.8, 0);
      head.userData = { part: 'head' };
      enemyGroup.add(head);
      enemyHitboxes.push(head);

      // Torso
      const torso = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.2, 0.4), bodyMat);
      torso.position.set(0, 1.9, 0);
      torso.userData = { part: 'body' };
      enemyGroup.add(torso);
      enemyHitboxes.push(torso);

      // Limbs
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

    // 4. PointerLock Direct Binding (시작 화면 제거)
    const controls = new THREE.PointerLockControls(camera, document.body);

    // 캔버스 자체를 클릭하면 별도 안내창 없이 바로 마우스 고정
    renderer.domElement.addEventListener('click', () => {
      if (!controls.isLocked) {
        controls.lock();
      }
    });

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

    // 5. Shooting (Mouse Left Click)
    const raycaster = new THREE.Raycaster();
    const hitLog = document.getElementById('hit-log');

    document.addEventListener('mousedown', (e) => {
      if (!controls.isLocked || e.button !== 0 || enemyHP <= 0 || playerHP <= 0) return;

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
          hitLog.innerText = "💥 적 피격! (10 데미지)";
          hitLog.style.color = "#ffcc00";
        }

        enemyHP = Math.max(0, enemyHP - damage);
        document.getElementById('enemy-hp').innerText = enemyHP;

        enemyHitboxes.forEach(part => part.material.color.setHex(0xffffff));
        setTimeout(() => {
          enemyHitboxes.forEach(part => {
            if (part.userData.part === 'head') part.material.color.setHex(0xffdbac);
            else part.material.color.setHex(0xcc3333);
          });
        }, 80);

        if (enemyHP <= 0) {
          scene.remove(enemyGroup);
          hitLog.innerText = "🏆 적을 처치하고 승리했습니다!";
          hitLog.style.color = "#00ff00";
        }
      }
    });

    // 6. Physics & Collision Systems
    camera.position.set(0, 2, 0);
    let velocityY = 0;
    const gravity = 25.0;

    function checkWallCollision(newPos) {
      const playerRadius = 0.6;
      for (let wall of wallObjects) {
        const box = new THREE.Box3().setFromObject(wall);
        const playerBox = new THREE.Box3(
          new THREE.Vector3(newPos.x - playerRadius, newPos.y - 1.5, newPos.z - playerRadius),
          new THREE.Vector3(newPos.x + playerRadius, newPos.y + 0.5, newPos.z + playerRadius)
        );

        if (box.intersectsBox(playerBox)) {
          return true;
        }
      }
      return false;
    }

    // 7. AI Attack Loop
    let lastAIShotTime = 0;

    function aiBehavior(delta) {
      if (enemyHP <= 0 || playerHP <= 0) return;

      enemyGroup.lookAt(camera.position.x, enemyGroup.position.y, camera.position.z);
      const distance = enemyGroup.position.distanceTo(camera.position);

      const aiEyePos = enemyGroup.position.clone().add(new THREE.Vector3(0, 2.5, 0));
      const dirToPlayer = camera.position.clone().sub(aiEyePos).normalize();
      
      const sightRay = new THREE.Raycaster(aiEyePos, dirToPlayer, 0, distance);
      const wallIntersects = sightRay.intersectObjects(wallObjects);

      if (wallIntersects.length === 0) {
        if (distance > 6) {
          enemyGroup.translateZ(2.5 * delta);
        }

        const now = clock.getElapsedTime();
        if (now - lastAIShotTime > 1.2) {
          lastAIShotTime = now;

          playerHP = Math.max(0, playerHP - 10);
          document.getElementById('player-hp').innerText = playerHP;

          hitLog.innerText = "⚠️ 적의 총에 맞았습니다! (-10)";
          hitLog.style.color = "#ff3333";

          if (playerHP <= 0) {
            hitLog.innerText = "💀 플레이어가 사망했습니다. (게임 오버)";
            controls.unlock();
          }
        }
      } else {
        enemyGroup.translateZ(1.5 * delta);
      }
    }

    // 8. Main Game Loop
    const clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);

      const delta = clock.getDelta();

      if (controls.isLocked && playerHP > 0) {
        const moveSpeed = 8.0 * delta;

        const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
        forward.y = 0;
        forward.normalize();

        const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
        right.y = 0;
        right.normalize();

        const moveVector = new THREE.Vector3();
        if (moveState.forward) moveVector.add(forward);
        if (moveState.backward) moveVector.sub(forward);
        if (moveState.right) moveVector.add(right);
        if (moveState.left) moveVector.sub(right);

        if (moveVector.lengthSq() > 0) {
          moveVector.normalize().multiplyScalar(moveSpeed);

          const targetPosX = camera.position.clone();
          targetPosX.x += moveVector.x;
          if (!checkWallCollision(targetPosX)) {
            camera.position.x = targetPosX.x;
          }

          const targetPosZ = camera.position.clone();
          targetPosZ.z += moveVector.z;
          if (!checkWallCollision(targetPosZ)) {
            camera.position.z = targetPosZ.z;
          }
        }

        // 낙하 물리 (Gravity Engine)
        const downRay = new THREE.Raycaster(camera.position, new THREE.Vector3(0, -1, 0), 0, 10);
        const hits = downRay.intersectObjects(groundObjects);

        if (hits.length > 0) {
          const targetY = hits[0].point.y + 2.0;

          if (camera.position.y > targetY) {
            velocityY -= gravity * delta;
            camera.position.y += velocityY * delta;

            if (camera.position.y <= targetY) {
              camera.position.y = targetY;
              velocityY = 0;
            }
          } else {
            camera.position.y = targetY;
            velocityY = 0;
          }
        } else {
          velocityY -= gravity * delta;
          camera.position.y += velocityY * delta;
        }
      }

      aiBehavior(delta);

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
