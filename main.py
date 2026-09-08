<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>간단한 3D FPS 게임</title>
  <style>
    body {
      margin: 0;
      overflow: hidden;
      font-family: sans-serif;
    }
    /* 크로스헤어(십자선) */
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
    }
    /* UI (적 체력 표시) */
    #ui {
      position: absolute;
      top: 20px;
      left: 20px;
      color: white;
      font-size: 20px;
      background: rgba(0, 0, 0, 0.5);
      padding: 10px 20px;
      border-radius: 5px;
      pointer-events: none;
    }
    /* 시작 안내 화면 */
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
    }
  </style>
  <!-- Three.js 및 PointerLockControls 라이브러리 -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/PointerLockControls.js"></script>
</head>
<body>

  <div id="crosshair"></div>
  <div id="ui">적 체력: <span id="hp">100</span> / 100</div>
  <div id="instructions">
    <p>클릭하여 게임 시작</p>
    <p style="font-size: 16px;">이동: WASD | 사격: 마우스 좌클릭 | 화면 전환: 마우스 이동</p>
  </div>

  <script>
    // 1. 기본 씬, 카메라, 렌더러 설정
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87ceeb); // 하늘색

    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    // 조명 추가
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(10, 20, 10);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x404040));

    // 바닥 생성
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
    enemy.position.set(0, 2, -15); // 플레이어 정면에 배치
    scene.add(enemy);

    // 3. 컨트롤 및 입력 처리 (WASD + 마우스 시점 전환)
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

    // WASD 이동 키 상태
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

    // 4. 발사 기능 (마우스 좌클릭) - Raycaster 활용
    const raycaster = new THREE.Raycaster();
    
    document.addEventListener('mousedown', (e) => {
      if (!controls.isLocked || e.button !== 0) return; // 포인터가 잠겨있고 좌클릭일 때만 실행

      // 카메라 중심에서 화면 정면으로 레이(광선) 발사
      raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
      const intersects = raycaster.intersectObject(enemy);

      if (intersects.length > 0 && enemyHP > 0) {
        // 적에 적중 시 데미지 10 적용
        enemyHP -= 10;
        document.getElementById('hp').innerText = enemyHP;

        // 적 피격 시 피드백 (잠시 하얗게 변함)
        enemy.material.color.setHex(0xffffff);
        setTimeout(() => enemy.material.color.setHex(0xff0000), 100);

        // 체력이 0 이하가 되면 적 처치
        if (enemyHP <= 0) {
          scene.remove(enemy);
          document.getElementById('ui').innerText = "적 처치 완료!";
        }
      }
    });

    // 초기 카메라 위치
    camera.position.y = 2;

    // 5. 게임 루프 (이동 및 간단한 AI 루틴)
    const clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const moveSpeed = 10.0 * delta;

      // WASD 이동
      if (controls.isLocked) {
        if (moveState.forward) controls.moveForward(moveSpeed);
        if (moveState.backward) controls.moveForward(-moveSpeed);
        if (moveState.left) controls.moveRight(-moveSpeed);
        if (moveState.right) controls.moveRight(moveSpeed);
      }

      // 간단한 AI: 적이 살아있을 경우 플레이어를 천천히 바라보고 다가옴
      if (enemyHP > 0) {
        enemy.lookAt(camera.position.x, enemy.position.y, camera.position.z);
        
        // 플레이어와의 거리가 3 이상일 때 다가옴
        const distance = enemy.position.distanceTo(camera.position);
        if (distance > 3) {
          enemy.translateZ(1.5 * delta);
        }
      }

      renderer.render(scene, camera);
    }

    animate();

    // 창 크기 변경 대응
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  </script>
</body>
</html>
