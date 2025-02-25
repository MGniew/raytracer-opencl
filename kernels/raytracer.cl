struct Material {
    float3 ambient;
    float3 diffuse;
    float3 specular;
    float3 emissive;
    float3 texture_ambient;
    float3 texture_diffuse;
    float3 texture_specular;
    float3 texture_bump;
    float transparency;
    float density;
    float shininess;
    float reflectiveness;
}; 

struct Texture { uchar* data;
    int width;
    int height;
};

struct Sphere {
    float3 position;
    float radius;
    struct Material material;
};

struct Triangle {
    float3 pointA;
    float3 pointB;
    float3 pointC;
    float3 normalA;
    float3 normalB;
    float3 normalC;
    float4 textureA;
    float4 textureB;
    float4 textureC;
    struct Material material;
};

struct Camera {
    float3 position;
    float3 topLeftCorner;
    float3 rightVector;
    float3 upVector;
    float worldWidth;
    float worldHeight;
    float zFar;
};

struct Light {
    float3 position;
    float3 ambient;
    float3 diffuse;
    float3 specular;
};

struct RayTask {
    float3 direction;
    float3 origin;
    float mult;
    float depth;
};

void push(__private uint* stack, uint value) {

    uint bufLen = 64;
    uint nextIndex=stack[0]%bufLen+2;
    stack[nextIndex]=value;
    stack[0] += 1;
}

bool empty(__private uint* stack) {
    return (stack[0] == stack[1]);
}

uint pop(__private uint* stack)
{
    uint bufLen=64;
    uint ptr=stack[1]%bufLen+2;
    uint returnValue=stack[ptr];
    stack[ptr]=0;
    stack[1] += 1;
    return returnValue;
}


float intersect_sphere(
        __constant struct Sphere* sphere,
        const float3 origin,
        const float3 direction) {

    float3 rayToCenter = origin - sphere->position;
    float b = dot(rayToCenter, direction);
    float c = dot(rayToCenter, rayToCenter) - sphere->radius * sphere->radius;

    if (c > 0.0001f && b > 0.0001f) {
        return -1;
    }

    float delta = b*b - c;
    if (delta < 0.0001f) {
        return -1;
    }

    delta = sqrt(delta);
    float distance = -b - delta;
    if (distance < 0.0001f) {
        distance = -b + delta;
    }
    return distance;
}

void push_struct(uint *stack, struct RayTask task) {
    uint* p = (uint*)&task;
    for (int i = 0; i < sizeof(struct RayTask) / 4; i++) {
        push(stack, p[i]);
    }
}

struct RayTask pop_struct(uint *stack) {
    uint p[sizeof(struct RayTask) / 4];
    for (int i = 0; i < sizeof(struct RayTask) / 4; i++) {
        p[i] = pop(stack);
    }

    return *((struct RayTask*)p);
}

float intersect_triagle(
        __constant struct Triangle* triangle,
        const float3 origin,
        const float3 direction) {

    float3 v0v1 = triangle->pointB - triangle->pointA;
    float3 v0v2 = triangle->pointC - triangle->pointA;
    float3 pvec = cross(direction, v0v2);
    float u, v, dist;

    float det = dot(v0v1, pvec);
    if (det < 0.0001f && det > -0.0001f) return -1;

    float invDet = 1.0f/det;
    float3 tvec = origin - triangle->pointA; u = dot(tvec, pvec) * invDet;
    if (u < -0.0001f || u > 1 + 0.0001f) return -1;

    float3 qvec = cross(tvec, v0v1);
    v = dot(direction, qvec)  * invDet;
    if (v < -0.0001f || u + v > 1 + 0.0001f) return -1;

    dist = dot(v0v2, qvec) * invDet;
    if (dist < 0.0001f)
        dist = -1;

    return dist;
}

float3 getSphereNormal(__constant struct Sphere* sphere, __private float3 crossPoint) {
    return normalize(crossPoint - sphere->position);
}

float3 getSphereColor(
        __constant struct Sphere* sphere,
        __constant struct Light* lights,
        __private int nLights,
        __private float3 crossPoint,
        __private float3 observationVector,
        __private float3 normalVector) {

    if (dot(observationVector, normalVector) < 0) {
        normalVector = - (normalVector);
    }

    float3 resultColor = sphere->material.ambient * (float3)(0.4f, 0.4f, 0.4f); // ...* global ambient
    for (int i = 0; i < nLights; i++) {
        float3 lightVector = normalize(lights[i].position - crossPoint);
        float n_dot_l = dot(lightVector, normalVector);
        float3 reflectionVector = normalize(lightVector - (normalVector) * 2*n_dot_l);
        float v_dot_r = dot(reflectionVector, observationVector);
        if (v_dot_r < 0) {
            v_dot_r = 0;
        }

        if(n_dot_l > 0.0001f) {//and no in shadow...
            resultColor += sphere->material.diffuse * lights[i].diffuse * n_dot_l +
                sphere->material.specular * lights[i].specular * pow(v_dot_r, 30) + //specShin
                sphere->material.ambient * lights[i].ambient;
        }
    }
    return resultColor;

}

float3 getTriangleNormal(
        __constant struct Triangle* triangle,
        __private float3 crossPoint,
        __private float3 *barVector) {

    float3 ba = triangle->pointB - triangle->pointA;
    float3 ca = triangle->pointC - triangle->pointA;
    float3 pa = crossPoint - triangle->pointA;

    float d00 = dot(ba, ba);
    float d01 = dot(ba, ca);
    float d11 = dot(ca, ca);
    float d20 = dot(pa, ba);
    float d21 = dot(pa, ca);
    float denom = d00 * d11 - d01 * d01;
    float v = (d11 * d20 - d01 * d21) / denom;
    float w = (d00 * d21 - d01 * d20) / denom;
    float u = 1 - v - w;

    barVector->x = u;
    barVector->y = v;
    barVector->z = w;

    return normalize(triangle->normalA*u + triangle->normalB*v + triangle->normalC*w);
}

float3 getColorTexture(
        float4 coordinates,
        float3 texture,
        read_only image2d_array_t textures) {

    float width = texture.y;
    float height = texture.z;
    coordinates.x = coordinates.x * width;
    coordinates.y = coordinates.y * height;

    if (coordinates.x > 0) {
        coordinates.x = fmod(coordinates.x, width);
    } else {
        coordinates.x -= width * floor(coordinates.x/width);
    }
    if (coordinates.y > 0) {
        coordinates.y = fmod(coordinates.y, height);
    } else {
        coordinates.y -= height * floor(coordinates.y/height);
    }

    const sampler_t sampler = CLK_NORMALIZED_COORDS_FALSE | CLK_ADDRESS_REPEAT | CLK_FILTER_LINEAR;
    float4 _diffuse = read_imagef(
            textures, sampler,
            (float4)(coordinates.x, coordinates.y, texture.x, 0.0f));
    return (float3)(_diffuse.x, _diffuse.y, _diffuse.z);
}

bool isInShadow(__constant struct Triangle* triangles,
                float nTriangles,
                float dist,
                float3 direction,
                float3 origin) {

    for(int i = 0; i < nTriangles; i++) {
        float tempDist = intersect_triagle(triangles + i, origin, direction);
        if (tempDist > 0.0001f && tempDist < dist) {
            return true;
        }
    }
    return false;
}

float3 getTriangleColor(
        __constant struct Triangle* triangles,
        int nTriangles,
        __constant struct Triangle* triangle,
        __constant struct Light* lights,
        __private int nLights,
        __private float3 crossPoint,
        __private float3 observationVector,
        __private float3 normalVector,
        __private float3 barVector,
        read_only image2d_array_t textures) {

    float4 coordinates;
    float3 diffuse = triangle->material.diffuse;
    float3 specular = triangle->material.specular;
    float3 ambient = triangle->material.ambient;
    if (triangle->material.texture_diffuse.x >= 0.0f ||
        triangle->material.texture_ambient.x >= 0.0f ||
        triangle->material.texture_specular.x >= 0.0f) {

        coordinates = (triangle->textureA * barVector.x + 
                       triangle->textureB * barVector.y +
                       triangle->textureC * barVector.z);

        if (triangle->material.texture_diffuse.x >= 0.0f) {
            diffuse *= getColorTexture(coordinates, triangle->material.texture_diffuse, textures);
        }
        if (triangle->material.texture_ambient.x >= 0.0f) {
            ambient *= getColorTexture(coordinates, triangle->material.texture_ambient, textures);
        }
        if (triangle->material.texture_specular.x >= 0.0f) {
            specular *= getColorTexture(coordinates, triangle->material.texture_specular, textures);
        }
    }

    if (dot(observationVector, normalVector) < 0) {
        normalVector = -normalVector; 
    }

    float3 resultColor = ambient * (float3)(0.6f, 0.6f, 0.6f);
    for (int i = 0; i < nLights; i++) {
        float3 lightVector = normalize(lights[i].position - crossPoint);
        float n_dot_l = dot(lightVector, normalVector);
        float3 reflectionVector = normalize(-lightVector - normalVector * 2*n_dot_l);

        float dist = distance(crossPoint, lights[i].position);
        if(n_dot_l > 0.0001f && !isInShadow(triangles, nTriangles, dist, lightVector, crossPoint)) {
            float v_dot_r = dot(reflectionVector, observationVector);
            if (v_dot_r < 0) {
                v_dot_r = 0;
            }
            resultColor += diffuse * lights[i].diffuse * n_dot_l +
                specular * lights[i].specular * pow(v_dot_r, triangle->material.shininess) +
                ambient * lights[i].ambient;
        }
    }
    return resultColor;

}

__constant struct Sphere* getClosestSphere(
        __constant struct Sphere* spheres,
        const int n_spheres,
        __private float* max_dist,
        __private float3 origin,
        __private float3 direction) {

    __constant struct Sphere* sphere = 0;
    float tempDist = *max_dist;
    for(int i = 0; i < n_spheres; i++) {
        tempDist = intersect_sphere(spheres + i, origin, direction);
        if (tempDist > 0.0001f) {
            if (tempDist < *max_dist) {
                sphere = spheres + i ;
                *max_dist = tempDist;
            }
        }
    }
    return sphere;
}

__constant struct Triangle* getClosestTriangle(
        __constant struct Triangle* triangles,
        const int n_triangles,
        __private float* max_dist,
        __private float3 origin,
        __private float3 direction) {

    __constant struct Triangle* triangle = 0;
    float tempDist = *max_dist;
    for(int i = 0; i < n_triangles; i++) {
        tempDist = intersect_triagle(triangles + i, origin, direction);
        if (tempDist > 0.0001f) {
            if (tempDist < *max_dist) {
                triangle = triangles + i;
                *max_dist = tempDist;
            }
        }
    }
    return triangle;
}


float3 get_reflected_ray(float3 direction, float3 normalVector) {
    float n_dot_l = dot(direction, normalVector);
    return normalize(direction - normalVector * 2*n_dot_l);
}

float3 get_refracted_ray(float3 direction, float3 normalVector, float a, float b) {
    float r;
    float cosa = dot(direction, normalVector);
    if (cosa < 0) {
        cosa = -cosa;
        r = b/a;
    }
    else {
        normalVector = -normalVector;
        r = a/b;
    }
    float k = 1 - r*r * (1 - cosa*cosa);
    return normalize(direction*r + normalVector*(r*cosa - sqrt(k)));
}

float3 trace(
        float3 origin,
        float3 direction,
        const int zFar,
        __constant struct Light* lights,
        const int nLights,
        __constant struct Sphere* spheres,
        const int n_spheres,
        __constant struct Triangle* triangles,
        const int n_triangles,
        read_only image2d_array_t textures){

    float3 color = (float3)(0,0,0);
    float mult = 1;
    float depth = 0;
    uint stack[100];
    stack[0] = 0;
    stack[1] = 0;

    struct RayTask task = {direction, origin, mult, depth};
    push_struct(stack, task);

    while(!empty(stack)) {   
        task = pop_struct(stack);
        origin = task.origin;
        direction = task.direction;
        depth = task.depth;
        mult = task.mult;

        float dist = zFar;
        __constant struct Sphere* sphere = getClosestSphere(spheres, n_spheres,
                                                 &dist, origin, direction);
        __constant struct Triangle* triangle = getClosestTriangle(triangles, n_triangles,
                                                 &dist, origin, direction);

        __private float3 normalVector;
        float3 phongColor = (float3)(0, 0, 0);
        origin = origin + direction * dist;

        if (triangle) {
            float3 barVector;
            normalVector = getTriangleNormal(triangle, origin, &barVector);

            if (triangle->material.transparency > 0) {
                float3 new_ray = get_refracted_ray(direction, normalVector, triangle->material.density, 1.0f);
                if (depth < 3 && mult * triangle->material.transparency > 0.05) {
                    struct RayTask task = {new_ray, origin, mult * triangle->material.transparency, depth+1};
                    push_struct(stack, task);
                }
            }
            if (triangle->material.reflectiveness > 0) {
                float3 new_ray = get_reflected_ray(direction, normalVector);
                if (depth < 2 && mult * triangle->material.reflectiveness > 0.05) {
                    struct RayTask task = {new_ray, origin, mult * triangle->material.reflectiveness, depth+1};
                    push_struct(stack, task);
                }
                mult = 1 - triangle->material.reflectiveness;
            }
            if (triangle->material.reflectiveness < 1 && triangle->material.transparency == 0) {
                phongColor = getTriangleColor(
                        triangles, n_triangles,
                        triangle, lights,
                        nLights,
                        origin,
                        -direction,
                        normalVector,
                        barVector,
                        textures);
            }
            color += mult * phongColor;
        }

        else if (sphere){
            normalVector = getSphereNormal(sphere, origin);
            color += mult * getSphereColor(
                    sphere,
                    lights,
                    nLights,
                    origin,
                    -direction,
                    normalVector);
        }
        else {
            color += mult * (float3)(0.0f, 0.7f, 0.95f);
            break;
        }
        mult *= 0.25f;
        direction = get_reflected_ray(direction, normalVector);
    }
    return color;
}

float3 getCameraRay(
        __constant struct Camera* camera,
        const int pixelX,
        const int pixelY,
        const int pixelWidth,
        const int pixelHeight,
        const int sample) { 
    float distanceX = pixelX/(float)pixelWidth;
    float distanceY = pixelY/(float)pixelHeight;
    float3 worldPixel = camera->topLeftCorner + distanceX * camera->worldWidth * camera->rightVector;
    worldPixel -= distanceY * camera->worldHeight * camera->upVector;

    switch(sample) {

        case 0:
            break;

        case 1:
            worldPixel += 1/(2*(float)pixelWidth) * camera->worldHeight * camera->upVector;
            worldPixel += 1/2*(float)pixelHeight * camera->worldWidth * camera->rightVector;
            break;

        case 2:
            worldPixel -= 1/(2*(float)pixelWidth) * camera->worldHeight * camera->upVector;
            worldPixel += 1/(2*(float)pixelHeight) * camera->worldWidth * camera->rightVector;
            break;
        case 3:
            worldPixel += 1/(2*(float)pixelWidth) * camera->worldHeight * camera->upVector;
            worldPixel -= 1/(2*(float)pixelHeight) * camera->worldWidth * camera->rightVector;
            break;
        case 4:
            worldPixel -= 1/(2*(float)pixelWidth) * camera->worldHeight * camera->upVector;
            worldPixel -= 1/(2*(float)pixelHeight) * camera->worldWidth * camera->rightVector;
            break;
        case 5:
            worldPixel += 1/(2*(float)pixelWidth) * camera->worldHeight * camera->upVector;
            break;
        case 6:
            worldPixel -= 1/(2*(float)pixelWidth) * camera->worldHeight * camera->upVector;
            break;
        case 7:
            worldPixel += 1/(2*(float)pixelHeight) * camera->worldWidth * camera->rightVector;
            break;
        case 8:
            worldPixel -= 1/(2*(float)pixelHeight) * camera->worldWidth * camera->rightVector;
            break;


    }

    return normalize(worldPixel - camera->position);
}

__kernel void get_image(__constant struct Camera* camera,
        __constant struct Light* lights,
        const int nLights,
        __constant struct Sphere* spheres,
        const int nSpheres,
        __constant struct Triangle* triangles,
        const int nTriangles,
        const int noise,
        read_only image2d_array_t textures,
        __global uchar* output) {

    int pixelX = get_global_id(0);
    int pixelY = get_global_id(1);
    int pixelWidth = get_global_size(0) * noise;
    int pixelHeight = get_global_size(1);

    if (noise > 1) {
        pixelX += pixelX * (noise - 1);
        pixelX += pixelY % noise;
    }

    int samples = 1;
    float3 result = (float3)(0.0f, 0.0f, 0.0f);

    for(int i = 0; i < samples; i++) {

    result += trace(camera->position,
        getCameraRay(camera, pixelX,
            pixelY, pixelWidth,
            pixelHeight, i),
        camera->zFar,
        lights, nLights,
        spheres, nSpheres,
        triangles, nTriangles,
        textures);
    }

    result  = result/samples;

    result = clamp(result, 0.0f, 1.0f);
    output[pixelY * pixelWidth * 3 + pixelX * 3 ] = convert_uchar(result.x * 255);
    output[pixelY * pixelWidth * 3 + pixelX * 3 + 1] = convert_uchar(result.y * 255);
    output[pixelY * pixelWidth * 3 + pixelX * 3 + 2] = convert_uchar(result.z * 255);
}
