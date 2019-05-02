struct Material {
    float3 ambience;
    float3 diffuse;
    float3 specular;
    float texture_num;
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
    float3 textureA;
    float3 textureB;
    float3 textureC;
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

float3 getSphereColor(
        __constant struct Sphere* sphere,
        __constant struct Light* lights,
        __private int nLights,
        __private float3 crossPoint,
        __private float3 observationVector,
        __private float3* normalVector) {

    *normalVector = normalize(crossPoint - sphere->position);
    if (dot(observationVector, *normalVector) < 0) {
        *normalVector = - (*normalVector);
    }
    float3 resultColor = sphere->material.ambience * (float3)(0.4f, 0.4f, 0.4f); // ...* global ambience
    for (int i = 0; i < nLights; i++) {
        float3 lightVector = normalize(lights[i].position - crossPoint);
        float n_dot_l = dot(lightVector, *normalVector);
        float3 reflectionVector = normalize(lightVector - (*normalVector) * 2*n_dot_l);
        float v_dot_r = dot(reflectionVector, observationVector);
        if (v_dot_r < 0) {
            v_dot_r = 0;
        }

        if(n_dot_l > 0.0001f) {//and no in shadow...
            resultColor += sphere->material.diffuse * lights[i].diffuse * n_dot_l +
                sphere->material.specular * lights[i].specular * pow(v_dot_r, 30) + //specShin
                sphere->material.ambience * lights[i].ambience;
        }
    }
    return resultColor;

}

float3 getTriangleColor(
        __constant struct Triangle* triangle,
        __constant struct Light* lights,
        __private int nLights,
        __private float3 crossPoint,
        __private float3 observationVector,
        __private float3* normalVector,
        read_only image2d_array_t textures) {

    float3 ab = triangle->pointA - triangle->pointB;
    float3 bc = triangle->pointB - triangle->pointC;
    float3 ca = triangle->pointC - triangle->pointA;
    float3 ap = triangle->pointA - crossPoint;
    float3 bp = triangle->pointB - crossPoint;
    float abArea = length(cross(ab, ap))/2;
    float bcArea = length(cross(bc, bp))/2;
    float caArea = length(cross(ca, ap))/2;

    float tArea = length(cross(ab, bc))/2;

    *normalVector = (triangle->normalA * bcArea + triangle->normalB * caArea + 
                triangle->normalC * abArea) / tArea;

    //float3 diffuse = triangle->material.diffuse;
    float3 diffuse = (float3)(0.0f, 0.0f, 0.0f);
    if (triangle->material.texture_num >= 0.0f) {

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
        float3 coordinates = (triangle->textureA * u + triangle->textureB * v +
           triangle->textureC * w);

        //float3 coordinates = (triangle->textureA * bcArea + triangle->textureB * caArea +
        //   triangle->textureC * abArea) / tArea;
        const sampler_t sampler = CLK_NORMALIZED_COORDS_FALSE | CLK_ADDRESS_CLAMP_TO_EDGE | CLK_FILTER_LINEAR;
        float4 _diffuse = read_imagef(
                textures, sampler,
                (float4)(coordinates.x, coordinates.y, triangle->material.texture_num, 0.0f));
        diffuse = (float3)(_diffuse.x, _diffuse.y, _diffuse.z);
        return diffuse;
    }


    *normalVector = normalize(*normalVector);

    if (dot(observationVector, *normalVector) < 0) {
        *normalVector = - (*normalVector); 
    }

    //float3 resultColor = triangle->material.ambience * (float3)(0.4f, 0.4f, 0.4f); // ...* global ambience
    float3 resultColor = diffuse; // ...* global ambience

    for (int i = 0; i < nLights; i++) {
        float3 lightVector = normalize(lights[i].position - crossPoint);
        float n_dot_l = dot(lightVector, *normalVector);
        float3 reflectionVector = normalize(lightVector - *normalVector * 2*n_dot_l);
        float v_dot_r = dot(reflectionVector, observationVector);
        if (v_dot_r < 0) {
            v_dot_r = 0;
        }

        if(n_dot_l > 0.0001f) {//and no in shadow...
            resultColor += diffuse * lights[i].diffuse * n_dot_l +
                triangle->material.specular * lights[i].specular * pow(v_dot_r, 30) + //specShin
                triangle->material.ambience * lights[i].ambience;
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
    for (int j = 0; j < 1; j ++) {
        float dist = zFar;
        __constant struct Sphere* sphere = getClosestSphere(spheres, n_spheres,
                                                 &dist, origin, direction);
        __constant struct Triangle* triangle = getClosestTriangle(triangles, n_triangles,
                                                 &dist, origin, direction);

        __private float3 normalVector;
        if (triangle) {
            origin = origin + direction * dist;
            color += mult * getTriangleColor(
                    triangle,
                    lights,
                    nLights,
                    origin,
                    direction,
                    &normalVector,
                    textures);
        }
        else if (sphere){
            origin = origin + direction * dist;
            color += mult * getSphereColor(
                    sphere,
                    lights,
                    nLights,
                    origin,
                    direction,
                    &normalVector);
        }
        else {
            color += mult * (float3)(0.5f, 0.5f, 0.5f);
            break;
        }
        mult *= 0.25f;
        float n_dot_l = dot(direction, normalVector);
        direction = normalize(direction - normalVector * 2*n_dot_l);
    }
    return color;
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

    float3 result = trace(camera->position,
            getCameraRay(camera, pixelX,
                pixelY, pixelWidth,
                pixelHeight),
            camera->zFar,
            lights, nLights,
            spheres, nSpheres,
            triangles, nTriangles,
            textures);

    result = clamp(result, 0.0f, 1.0f);
    output[pixelY * pixelWidth * 3 + pixelX * 3 ] = convert_uchar(result.x * 255);
    output[pixelY * pixelWidth * 3 + pixelX * 3 + 1] = convert_uchar(result.y * 255);
    output[pixelY * pixelWidth * 3 + pixelX * 3 + 2] = convert_uchar(result.z * 255);
   //     const sampler_t sampler = CLK_FILTER_NEAREST | CLK_NORMALIZED_COORDS_FALSE | CLK_ADDRESS_CLAMP_TO_EDGE;
   //     float4 result = read_imagef(
   //             textures, sampler,
   //             (float4)(pixelX, pixelY, 8, 0.0f));
   // output[pixelY * pixelWidth * 3 + pixelX * 3 ] = convert_uchar(result.x * 255);
   // output[pixelY * pixelWidth * 3 + pixelX * 3 + 1] = convert_uchar(result.y * 255);
   // output[pixelY * pixelWidth * 3 + pixelX * 3 + 2] = convert_uchar(result.z * 255);

}
