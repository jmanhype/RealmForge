"""Three.js code generator for scene visualization."""

from typing import Dict, List, Any, Optional
from textwrap import dedent
import json

from ...models.visualization import (
    SceneDefinition,
    ObjectDefinition,
    LightDefinition,
    CameraDefinition,
    Vector3,
    Color
)

class ThreeJSCodeGenerator:
    """Generator for Three.js scene code.
    
    This class handles:
    - Scene setup code generation
    - Object instantiation
    - Material and texture setup
    - Lighting configuration
    - Post-processing pipeline setup
    - Animation and interaction code
    """
    
    def __init__(self) -> None:
        """Initialize the code generator."""
        self.import_template = dedent("""
            import * as THREE from 'three';
            import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
            import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer';
            import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass';
            import { SSAOPass } from 'three/examples/jsm/postprocessing/SSAOPass';
            import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass';
            import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
        """).strip()
        
        self.scene_setup_template = dedent("""
            // Scene setup
            const scene = new THREE.Scene();
            {environment_code}
            
            // Renderer setup
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.shadowMap.enabled = {shadow_enabled};
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.outputEncoding = THREE.sRGBEncoding;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            document.body.appendChild(renderer.domElement);
            
            // Camera setup
            {camera_code}
            
            // Controls setup
            const controls = new OrbitControls(camera, renderer.domElement);
            controls.target.set({target_x}, {target_y}, {target_z});
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Asset loading
            const loader = new GLTFLoader();
            const textureLoader = new THREE.TextureLoader();
            const loadingManager = new THREE.LoadingManager();
            
            // Loading progress
            loadingManager.onProgress = (url, loaded, total) => {{
                const progress = (loaded / total * 100).toFixed(2);
                console.log(`Loading: ${progress}% (${url})`);
            }};
        """).strip()
        
        self.post_processing_template = dedent("""
            // Post-processing setup
            const composer = new EffectComposer(renderer);
            const renderPass = new RenderPass(scene, camera);
            composer.addPass(renderPass);
            
            {effect_passes}
        """).strip()
        
        self.animation_template = dedent("""
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                {update_code}
                composer.render();
            }}
            
            // Handle window resize
            window.addEventListener('resize', () => {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
                composer.setSize(window.innerWidth, window.innerHeight);
            }});
            
            // Start animation loop
            animate();
        """).strip()
    
    def generate_code(
        self,
        scene_def: SceneDefinition,
        quality_settings: Dict[str, Any]
    ) -> str:
        """Generate Three.js code for the scene.
        
        Args:
            scene_def: Scene definition
            quality_settings: Quality settings
            
        Returns:
            str: Generated Three.js code
        """
        code_parts = [
            self.import_template,
            "",
            "// Initialize scene",
            self._generate_scene_setup(scene_def, quality_settings),
            "",
            "// Add lights",
            self._generate_lights(scene_def.lights),
            "",
            "// Add objects",
            self._generate_objects(scene_def.objects),
            "",
            "// Setup post-processing",
            self._generate_post_processing(scene_def.post_processing, quality_settings),
            "",
            "// Animation and rendering",
            self._generate_animation(scene_def)
        ]
        
        return "\n".join(code_parts)
    
    def _generate_scene_setup(
        self,
        scene_def: SceneDefinition,
        quality_settings: Dict[str, Any]
    ) -> str:
        """Generate scene setup code.
        
        Args:
            scene_def: Scene definition
            quality_settings: Quality settings
            
        Returns:
            str: Generated setup code
        """
        camera = scene_def.camera
        environment_code = self._generate_environment(scene_def.environment)
        
        camera_code = dedent(f"""
            const camera = new THREE.{camera.type.capitalize()}Camera(
                {camera.fov},
                window.innerWidth / window.innerHeight,
                {camera.near},
                {camera.far}
            );
            camera.position.set({camera.position.x}, {camera.position.y}, {camera.position.z});
        """).strip()
        
        return self.scene_setup_template.format(
            environment_code=environment_code,
            camera_code=camera_code,
            shadow_enabled=str(quality_settings.get("shadows_enabled", True)).lower(),
            target_x=camera.target.x,
            target_y=camera.target.y,
            target_z=camera.target.z
        )
    
    def _generate_environment(self, environment: Dict[str, Any]) -> str:
        """Generate environment setup code.
        
        Args:
            environment: Environment settings
            
        Returns:
            str: Generated environment code
        """
        if not environment:
            return "scene.background = new THREE.Color(0x000000);"
            
        code_parts = []
        
        if "skybox" in environment:
            code_parts.append(dedent(f"""
                const skyboxLoader = new THREE.CubeTextureLoader();
                const skybox = skyboxLoader.load([
                    '{environment["skybox"]["px"]}',
                    '{environment["skybox"]["nx"]}',
                    '{environment["skybox"]["py"]}',
                    '{environment["skybox"]["ny"]}',
                    '{environment["skybox"]["pz"]}',
                    '{environment["skybox"]["nz"]}'
                ]);
                scene.background = skybox;
                scene.environment = skybox;
            """).strip())
        
        if "fog" in environment:
            fog = environment["fog"]
            if fog["type"] == "linear":
                code_parts.append(
                    f"scene.fog = new THREE.Fog("
                    f"0x{fog['color']:06x}, {fog['near']}, {fog['far']});"
                )
            elif fog["type"] == "exponential":
                code_parts.append(
                    f"scene.fog = new THREE.FogExp2("
                    f"0x{fog['color']:06x}, {fog['density']});"
                )
        
        return "\n".join(code_parts)
    
    def _generate_lights(self, lights: List[LightDefinition]) -> str:
        """Generate light setup code.
        
        Args:
            lights: List of light definitions
            
        Returns:
            str: Generated light code
        """
        code_parts = []
        
        for i, light in enumerate(lights):
            light_var = f"light_{i}"
            
            if light.type == "ambient":
                code_parts.append(
                    f"const {light_var} = new THREE.AmbientLight("
                    f"0x{light.color:06x}, {light.intensity});"
                )
            
            elif light.type == "directional":
                code_parts.extend([
                    f"const {light_var} = new THREE.DirectionalLight("
                    f"0x{light.color:06x}, {light.intensity});",
                    f"{light_var}.position.set({light.position.x}, "
                    f"{light.position.y}, {light.position.z});",
                    f"{light_var}.castShadow = {str(light.cast_shadows).lower()};"
                ])
                
                if light.cast_shadows:
                    code_parts.extend([
                        f"{light_var}.shadow.mapSize.width = {light.shadow_map_size};",
                        f"{light_var}.shadow.mapSize.height = {light.shadow_map_size};",
                        f"{light_var}.shadow.camera.near = 0.5;",
                        f"{light_var}.shadow.camera.far = 500;"
                    ])
            
            elif light.type == "point":
                code_parts.extend([
                    f"const {light_var} = new THREE.PointLight("
                    f"0x{light.color:06x}, {light.intensity});",
                    f"{light_var}.position.set({light.position.x}, "
                    f"{light.position.y}, {light.position.z});"
                ])
            
            code_parts.append(f"scene.add({light_var});")
            code_parts.append("")
        
        return "\n".join(code_parts)
    
    def _generate_objects(self, objects: List[ObjectDefinition]) -> str:
        """Generate object creation code.
        
        Args:
            objects: List of object definitions
            
        Returns:
            str: Generated object code
        """
        code_parts = []
        
        for i, obj in enumerate(objects):
            obj_var = f"object_{i}"
            
            if obj.model_id:
                # Load GLTF model
                code_parts.extend([
                    f"// Load {obj.name}",
                    f"loader.load('{obj.model_id}', (gltf) => {{",
                    f"    const {obj_var} = gltf.scene;",
                    self._generate_object_properties(obj_var, obj),
                    "    scene.add(gltf.scene);",
                    "});"
                ])
            else:
                # Create basic geometry
                code_parts.extend([
                    f"// Create {obj.name}",
                    f"const {obj_var}_geometry = new THREE.{obj.geometry.type}("
                    f"{', '.join(str(p) for p in obj.geometry.parameters)});",
                    f"const {obj_var}_material = new THREE.{obj.material.type}({{",
                    f"    color: 0x{obj.material.color:06x},",
                    f"    metalness: {obj.material.metalness},",
                    f"    roughness: {obj.material.roughness}",
                    "});",
                    f"const {obj_var} = new THREE.Mesh("
                    f"{obj_var}_geometry, {obj_var}_material);",
                    self._generate_object_properties(obj_var, obj),
                    f"scene.add({obj_var});"
                ])
            
            code_parts.append("")
        
        return "\n".join(code_parts)
    
    def _generate_object_properties(self, obj_var: str, obj: ObjectDefinition) -> str:
        """Generate object property setup code.
        
        Args:
            obj_var: Object variable name
            obj: Object definition
            
        Returns:
            str: Generated property code
        """
        code_parts = []
        
        # Position, rotation, scale
        code_parts.extend([
            f"{obj_var}.position.set({obj.position.x}, {obj.position.y}, {obj.position.z});",
            f"{obj_var}.rotation.set({obj.rotation.x}, {obj.rotation.y}, {obj.rotation.z});",
            f"{obj_var}.scale.set({obj.scale.x}, {obj.scale.y}, {obj.scale.z});"
        ])
        
        # Shadows
        if obj.cast_shadows:
            code_parts.append(f"{obj_var}.castShadow = true;")
        if obj.receive_shadows:
            code_parts.append(f"{obj_var}.receiveShadow = true;")
        
        return "\n".join(code_parts)
    
    def _generate_post_processing(
        self,
        effects: List[Dict[str, Any]],
        quality_settings: Dict[str, Any]
    ) -> str:
        """Generate post-processing setup code.
        
        Args:
            effects: List of post-processing effects
            quality_settings: Quality settings
            
        Returns:
            str: Generated post-processing code
        """
        if not effects:
            return "// No post-processing effects"
            
        effect_passes = []
        
        for effect in effects:
            if effect["type"] == "ssao":
                effect_passes.extend([
                    "// Add SSAO",
                    "const ssaoPass = new SSAOPass(scene, camera);",
                    f"ssaoPass.kernelRadius = {effect['radius']};",
                    f"ssaoPass.minDistance = {effect.get('min_distance', 0.001)};",
                    f"ssaoPass.maxDistance = {effect.get('max_distance', 0.1)};",
                    "composer.addPass(ssaoPass);"
                ])
            
            elif effect["type"] == "bloom":
                effect_passes.extend([
                    "// Add bloom",
                    "const bloomPass = new UnrealBloomPass(",
                    "    new THREE.Vector2(window.innerWidth, window.innerHeight),",
                    f"    {effect['intensity']},  // Intensity",
                    f"    {effect.get('radius', 0.85)},  // Radius",
                    f"    {effect['threshold']}  // Threshold",
                    ");",
                    "composer.addPass(bloomPass);"
                ])
        
        return self.post_processing_template.format(
            effect_passes="\n".join(effect_passes)
        )
    
    def _generate_animation(self, scene_def: SceneDefinition) -> str:
        """Generate animation loop code.
        
        Args:
            scene_def: Scene definition
            
        Returns:
            str: Generated animation code
        """
        update_code = []
        
        # Add object animations
        for i, obj in enumerate(scene_def.objects):
            if obj.animation:
                update_code.append(f"object_{i}.rotation.y += 0.01;")
        
        # Add any additional update logic here
        
        return self.animation_template.format(
            update_code="\n    ".join(update_code) if update_code else "// No animations"
        ) 