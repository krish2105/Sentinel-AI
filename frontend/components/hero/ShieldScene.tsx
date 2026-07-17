"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Icosahedron, Line } from "@react-three/drei";
import * as THREE from "three";

// A single "attack" particle that streams toward the shield and either deflects
// (cyan) or slips through (red).
type Particle = {
  angle: number;
  radius: number;
  speed: number;
  breach: boolean;
  offset: number;
  y: number;
};

function Swarm({ count = 42 }: { count?: number }) {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const color = useMemo(() => new THREE.Color(), []);

  const particles = useMemo<Particle[]>(() => {
    return Array.from({ length: count }, (_, i) => ({
      angle: (i / count) * Math.PI * 2 + Math.random(),
      radius: 3.2 + Math.random() * 2.5,
      speed: 0.15 + Math.random() * 0.35,
      breach: Math.random() < 0.18, // ~18% slip through
      offset: Math.random() * Math.PI * 2,
      y: (Math.random() - 0.5) * 2.4,
    }));
  }, [count]);

  useFrame((state) => {
    const mesh = meshRef.current;
    if (!mesh) return;
    const t = state.clock.elapsedTime;
    particles.forEach((p, i) => {
      // Oscillate inward/outward; breach particles go closer to the core.
      const pulse = (Math.sin(t * p.speed + p.offset) + 1) / 2; // 0..1
      const minR = p.breach ? 0.6 : 1.75;
      const r = minR + (p.radius - minR) * pulse;
      const a = p.angle + t * 0.08;
      dummy.position.set(Math.cos(a) * r, p.y * pulse, Math.sin(a) * r);
      const scale = 0.05 + (1 - pulse) * 0.05;
      dummy.scale.setScalar(scale);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);

      const near = pulse < 0.25;
      if (p.breach && near) color.set("#FF4D5E");
      else if (near) color.set("#22E9D3");
      else color.set(p.breach ? "#ff8a94" : "#7cf2e4");
      mesh.setColorAt(i, color);
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, count]}>
      <sphereGeometry args={[1, 8, 8]} />
      <meshBasicMaterial toneMapped={false} />
    </instancedMesh>
  );
}

function Shield() {
  const group = useRef<THREE.Group>(null);
  const ring = useRef<THREE.Mesh>(null);
  const { pointer } = useThree();

  useFrame((state, delta) => {
    if (group.current) {
      group.current.rotation.y += delta * 0.15;
      // Mouse parallax (spring-ish lerp)
      group.current.rotation.x = THREE.MathUtils.lerp(
        group.current.rotation.x,
        pointer.y * 0.25,
        0.05
      );
      group.current.position.x = THREE.MathUtils.lerp(
        group.current.position.x,
        pointer.x * 0.3,
        0.05
      );
    }
    if (ring.current) {
      const s = 1 + Math.sin(state.clock.elapsedTime * 1.5) * 0.03;
      ring.current.scale.setScalar(s);
    }
  });

  const ringPoints = useMemo(() => {
    const pts: [number, number, number][] = [];
    for (let i = 0; i <= 64; i++) {
      const a = (i / 64) * Math.PI * 2;
      pts.push([Math.cos(a) * 2.1, 0, Math.sin(a) * 2.1]);
    }
    return pts;
  }, []);

  return (
    <group ref={group}>
      {/* Wireframe protected core */}
      <Icosahedron args={[1.4, 1]}>
        <meshBasicMaterial color="#22E9D3" wireframe transparent opacity={0.55} toneMapped={false} />
      </Icosahedron>
      <Icosahedron args={[1.15, 0]}>
        <meshBasicMaterial color="#0f6f66" wireframe transparent opacity={0.4} toneMapped={false} />
      </Icosahedron>
      {/* Barrier ring */}
      <mesh ref={ring} rotation={[Math.PI / 2.3, 0, 0]}>
        <torusGeometry args={[2.1, 0.012, 8, 80]} />
        <meshBasicMaterial color="#22E9D3" transparent opacity={0.5} toneMapped={false} />
      </mesh>
      <Line points={ringPoints} color="#22E9D3" lineWidth={0.6} transparent opacity={0.25} />
    </group>
  );
}

export default function ShieldScene() {
  return (
    <Canvas
      camera={{ position: [0, 0, 8], fov: 45 }}
      dpr={[1, 1.8]}
      gl={{ antialias: true, alpha: true }}
      style={{ background: "transparent" }}
    >
      <ambientLight intensity={0.5} />
      <Shield />
      <Swarm />
    </Canvas>
  );
}
