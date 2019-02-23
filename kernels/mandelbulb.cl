struct Camera {
    float3 position;
    float3 topLeftCorner;
    float3 rightVector;
    float3 upVector;
    float worldWidth;
    float worldHeight;
    float zFar;
};

struct Material {
    float3 ambience;
    float3 diffuse;
    float3 specular;
};

struct Light {
    float3 position;
    float3 ambience;
    float3 diffuse;
    float3 specular;
};

float3 getCameraRay(
        __constant struct Camera* camera,
        const int pixelX,
        const int pixelY,
        const int pixelWidth,
        const int pixelHeight) {

    float distanceX = pixelX/(float)pixelWidth;
    float distanceY = pixelY/(float)pixelHeight;
    float3 worldPixel = camera->topLeftCorner + distanceX * camera->worldWidth * camera->rightVector;
    worldPixel -= distanceY * camera->worldHeight * camera->upVector;
    return normalize(worldPixel - camera->position);
}


int checkIfPointInSet(private float3 point, const int n, const int reverse) {

    float x = point.x;
    float y = point.y;
    float z = point.z;

    for (int i=0; i<32; i++) { // 64

        float r = sqrt(x*x + y*y +z*z);
        float phi = atan2(y, x);
        float theta = acos(z/r);
        r = pow(r, n);

        x = r * sin(n * theta) * cos(n * phi) + point.x;
        y = r * sin(n * theta) * sin(n * phi) + point.y;
        z = r * cos(n * theta) + point.z;

		if (reverse == 1) {
			if (x*x + y*y + z*z < 2) {
				return 0;
			}
		} else {
			if (x*x + y*y + z*z > 2) {
				return 0;
			}
		}

    }
    return 1;
}

float intersect_mandelbulb(
    const float3 origin,
    const float3 direction,
    const float zFar,
    private float3* crossPoint,
    const int n,
    const int reverse) {

    private float step = 0.005f;  // 0.0005 best
    private float3 vec = origin;

    for (float dist = 0; dist<zFar; dist+=step) {
        vec = origin + direction * dist;

        if (checkIfPointInSet(vec, n, reverse) == 1) {
            *crossPoint = vec;
            return 1;
        }
    }
    return -1;
}

#define NUM_NORMALS 26
constant float3 basicNormals[NUM_NORMALS] = {
(float3)(1, 0, 0),
(float3)(-1, 0, 0),
(float3)(0, 1, 0),
(float3)(0, -1, 0),
(float3)(0, 0, 1),
(float3)(0, 0, -1),

(float3)(1, 1, 1),
(float3)(1, 1, -1),
(float3)(1, -1, 1),
(float3)(1, -1, -1),
(float3)(-1, 1, 1),
(float3)(-1, 1, -1),
(float3)(-1, -1, 1),
(float3)(-1, -1, -1),


(float3)(0, 1, 1),
(float3)(0, 1, -1),
(float3)(0, -1, 1),
(float3)(0, -1, -1),
(float3)(-1, 1, 0),
(float3)(1, -1, 0),
(float3)(-1, -1, 0),
(float3)(1, 1, 0),
(float3)(-1, 0, 1),
(float3)(1, 0, -1),
(float3)(-1, 0, -1),
(float3)(1, 0, 1),
};

float3 getNormalVector(private float3 point, const int n, const int reverse) {

    float3 result = (float3)(0, 0, 0);

    for (int i=0; i<NUM_NORMALS; i++) {
        if (checkIfPointInSet(point + basicNormals[i] * 0.01f, n, reverse) == 0) {
            result = result + basicNormals[i];
        }
    }

    if (result.x == 0 && result.y == 0 && result.z == 0) {
        result = point;
    }

    return normalize(result);
}

struct Material getMaterial(private float3 point) {

    struct Material material;
    // material.ambience = (float3)(0.7, 0.5, 0.2);
    // material.specular = (float3)(0.2, 0.2, 0.2);
    // material.diffuse = (float3)(0.2, 0.2, 0.2);
    material.ambience = normalize(point);
    material.specular = normalize(point);
    material.diffuse = normalize(point);

    return material;
}

float3 getColor(
        __constant struct Light* lights,
        __private int nLights,
        __private float3 crossPoint,
        __private float3 observationVector,
        __private float3* normalVector,
        const int n,
		const int reverse) {

    struct Material material = getMaterial(crossPoint);


    *normalVector = getNormalVector(crossPoint, n, reverse); //temp
    float3 resultColor = material.ambience * (float3)(0.4f, 0.4f, 0.4f);

    for (int i = 0; i < nLights; i++) {
        float3 lightVector = normalize(lights[i].position - crossPoint);
        float n_dot_l = dot(lightVector, *normalVector);
        float3 reflectionVector = normalize(lightVector - *normalVector * 2*n_dot_l);
        float v_dot_r = dot(reflectionVector, observationVector);
        if (v_dot_r < 0) {
            v_dot_r = 0;
        }

        if(n_dot_l > 0.0001f) {//and no in shadow...
            resultColor += material.diffuse * lights[i].diffuse * n_dot_l +
                material.specular * lights[i].specular * pow(v_dot_r, 30) + //specShin
                material.ambience * lights[i].ambience;
        }
    }

    return resultColor;
}


float3 trace(
        float3 origin,
        float3 direction,
        const int zFar,
        __constant struct Light* lights,
        const int nLights,
        const int n,
        const int reverse) {


    float3 color = (float3)(0,0,0);
    float mult = 1;
    for (int j = 0; j < 2; j ++) {

        __private float3 crossPoint;
        __private  float3 normalVector;
        float dist = intersect_mandelbulb(
           origin,
           direction,
           zFar,
           &crossPoint,
           n,
           reverse);

        if (dist >= 0) {
            color += mult * getColor(
                lights,
                nLights,
                crossPoint,
                direction,
                &normalVector,
                n,
                reverse);
        }
        else {
            color += mult * (float3)(1, 1, 1);
            break;
        }
        mult *= 0.25f;
        float n_dot_l = dot(direction, normalVector);
        direction = normalize(direction - normalVector * 2*n_dot_l);
    }
    return color;
}


__kernel void get_image(
        __constant struct Camera* camera,
        __constant struct Light* lights,
        const int nLights,
        const int n,
        const int reverse,
        __global int* output) {

    const int pixelX = get_global_id(0);
    const int pixelY = get_global_id(1);
    const int pixelWidth = get_global_size(0);
    const int pixelHeight = get_global_size(1);

    float3 result = trace(camera->position,
                getCameraRay(camera, pixelX,
                    pixelY, pixelWidth,
                    pixelHeight),
                camera->zFar,
                lights, nLights, n, reverse);

    result = fabs(result);
    if (result.x > 1)
        result.x = 1;
    if (result.y > 1)
        result.y = 1;
    if (result.z > 1)
        result.z = 1;

    // output[pixelY * pixelWidth + pixelX] = (int3)(1, 2, 3);
    output[pixelY * pixelWidth * 3 + pixelX * 3 ] = (int)(result.x * 254);
    output[pixelY * pixelWidth * 3 + pixelX * 3 + 1] = (int)(result.y * 254);
    output[pixelY * pixelWidth * 3 + pixelX * 3 + 2] = (int)(result.z * 254);
}
