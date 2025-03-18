// RealmForge Visualizer App

// API URLs
const API_BASE_URL = 'http://localhost:8001';
const SCENE_URL = `${API_BASE_URL}/visualization/scene`;
const CHARACTER_URL = `${API_BASE_URL}/visualization/character`;
const TEMPLATE_URL = `${API_BASE_URL}/visualization/template`;

// Three.js globals
let scene, camera, renderer, controls;
let currentModel = null;

// =======================================
// Initialization Functions
// =======================================

// Initialize Three.js environment
function initThreeJs() {
    console.log("Initializing ThreeJS environment");
    try {
        // Create scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x87ceeb);
        
        // Create camera (will be replaced by scene definition later)
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 5, 10);
        
        // Create renderer
        const container = document.getElementById('scene-container');
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);
        
        // Add orbit controls
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 0, 0);
        controls.update();
        
        // Add ambient light (will be replaced by scene definition)
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        
        // Add directional light (will be replaced by scene definition)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(5, 10, 5);
        directionalLight.castShadow = true;
        scene.add(directionalLight);
        
        // Add grid for reference
        const gridHelper = new THREE.GridHelper(20, 20);
        scene.add(gridHelper);
        
        // Add a simple cube to confirm the scene is working
        const geometry = new THREE.BoxGeometry(1, 1, 1);
        const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 });
        const cube = new THREE.Mesh(geometry, material);
        cube.position.y = 0.5;
        scene.add(cube);

        // Handle window resize
        window.addEventListener('resize', onWindowResize);
        
        // Start animation loop
        animate();
        console.log("ThreeJS initialization complete");
    } catch (error) {
        console.error("Error initializing ThreeJS:", error);
        alert("Failed to initialize 3D environment: " + error.message);
    }
}

// =======================================
// Core Scene Functions
// =======================================

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

// Handle window resize
function onWindowResize() {
    try {
        const container = document.getElementById('scene-container');
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    } catch (error) {
        console.error("Error handling window resize:", error);
    }
}

// Clear scene except for lights and grid
function clearScene() {
    console.log("Clearing scene");
    try {
        while(scene.children.length > 0) { 
            scene.remove(scene.children[0]); 
        }
        
        // Re-add grid
        const gridHelper = new THREE.GridHelper(20, 20);
        scene.add(gridHelper);
        
        // Add default lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(5, 10, 5);
        directionalLight.castShadow = true;
        scene.add(directionalLight);
        
        console.log("Scene cleared successfully");
    } catch (error) {
        console.error("Error clearing scene:", error);
    }
}

// =======================================
// API Call Functions  
// =======================================

// Generate scene API call
async function generateScene() {
    console.log("Generate Scene button clicked!");
    
    // Add loading indicator
    document.getElementById('generate-scene').disabled = true;
    document.getElementById('generate-scene').textContent = 'Generating...';
    
    const playerID = document.getElementById('player-id').value;
    const locationID = document.getElementById('location-id').value;
    const qualityLevel = document.getElementById('quality-level').value;
    
    console.log(`Generating scene with: player=${playerID}, location=${locationID}, quality=${qualityLevel}`);
    
    const requestData = {
        player_id: playerID,
        location_id: locationID,
        quality_level: qualityLevel,
        include_assets: true,
        renderer_settings: {}
    };
    
    try {
        console.log("Sending request to:", SCENE_URL);
        console.log("Request data:", JSON.stringify(requestData));
        
        // Fallback to mock data for testing purposes
        let data;
        
        try {
            const response = await fetch(SCENE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                console.warn(`API returned status: ${response.status}`);
                throw new Error(`API Error: ${response.status}`);
            }
            
            data = await response.json();
            console.log('Scene generation response:', data);
        } catch (apiError) {
            console.error("API call failed:", apiError);
            
            // Create mock data for testing
            console.log("Using fallback mock data for testing");
            
            // Add a forest scene if locationID includes "forest"
            if (locationID.includes("forest")) {
                clearScene();
                addForestContent();
                alert("Using mock forest data (API error: " + apiError.message + ")");
                return;
            } else if (locationID.includes("town")) {
                clearScene();
                addTownContent();
                alert("Using mock town data (API error: " + apiError.message + ")");
                return;
            } else {
                clearScene();
                addGenericContent();
                alert("Using mock generic data (API error: " + apiError.message + ")");
                return;
            }
        }
        
        // Apply scene data to Three.js scene
        if (data && data.scene_definition) {
            createEnvironment(data.scene_definition);
        } else {
            throw new Error("Invalid scene data returned from API");
        }
        
    } catch (error) {
        console.error('Error generating scene:', error);
        alert(`Failed to generate scene: ${error.message}`);
        clearScene();
        addGenericContent();
    } finally {
        // Reset button
        document.getElementById('generate-scene').disabled = false;
        document.getElementById('generate-scene').textContent = 'Generate Scene';
    }
}

// Generate character API call
async function generateCharacter() {
    console.log("Generate Character button clicked!");
    const characterID = document.getElementById('character-id').value;
    const characterType = document.getElementById('character-type').value;
    const characterClass = document.getElementById('character-class').value;
    const description = document.getElementById('character-description').value;
    
    const requestData = {
        character_id: characterID,
        character_type: characterType,
        character_class: characterClass,
        description: description,
        height: 1.8,
        build: 'average',
        quality_level: 'high',
        include_animations: true
    };
    
    try {
        const response = await fetch(CHARACTER_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Character generation response:', data);
        
        // Add character model to scene
        addCharacterModel(data);
        
    } catch (error) {
        console.error('Error generating character:', error);
        alert(`Failed to generate character: ${error.message}`);
    }
}

// Generate template API call
async function generateTemplate() {
    console.log("Generate Template button clicked!");
    const templateType = document.getElementById('template-type').value;
    const qualityLevel = document.getElementById('template-quality').value;
    
    const requestData = {
        template_type: templateType,
        quality_level: qualityLevel,
        template_parameters: {
            time_of_day: 'day',
            density: 'medium'
        }
    };
    
    try {
        const response = await fetch(TEMPLATE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Template generation response:', data);
        
        // Apply template to Three.js scene
        createEnvironment(data.scene_definition);
        
    } catch (error) {
        console.error('Error generating template:', error);
        alert(`Failed to generate template: ${error.message}`);
    }
}

// =======================================
// Event Listeners
// =======================================

// Initialize app
window.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded - initializing app");
    try {
        initThreeJs();
        
        // Add event listeners for buttons
        console.log("Setting up button event listeners");
        document.getElementById('generate-scene').addEventListener('click', generateScene);
        document.getElementById('generate-character').addEventListener('click', generateCharacter);
        document.getElementById('generate-template').addEventListener('click', generateTemplate);
        console.log("Button event listeners set up successfully");
    } catch (error) {
        console.error("Error in app initialization:", error);
        alert("Error initializing app: " + error.message);
    }
}); 