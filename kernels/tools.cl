__kernel void mean_filter(
        __global uchar* image) {

    int x = get_global_id(0);
    int y = get_global_id(1);
    int width = get_global_size(0) * 2;
    int height = get_global_size(1);

    x += x;
    x += (y + 1) % 2;

    uint r = 0;
    uint g = 0;
    uint b = 0;
    uint sum = 0;
    uint pos = (y * width + x) * 3;
    
    //naive method - could cache some values
    if (x + 1 < width) {
        r += image[pos + 3];
        g += image[pos + 4];
        b += image[pos + 5];
        sum += 1;}
    if (x - 1 > 0) {
        r += image[pos - 3];
        g += image[pos - 2];
        b += image[pos - 1];
        sum += 1;}
    if (y + 1 < height){
        r += image[pos + width * 3];
        g += image[pos + width * 3 + 1];
        b += image[pos + width * 3 + 2];
        sum += 1;}
    if (y - 1 > 0){
        r += image[pos - width * 3];
        g += image[pos - width * 3 + 1];
        b += image[pos - width * 3 + 2];
        sum += 1;}

    image[pos] = convert_uchar(r/sum);
    image[pos + 1] = convert_uchar(g/sum);
    image[pos + 2] = convert_uchar(b/sum);

}

float get_distance(float3 pixel_a, float3 pixel_b) {
    return distance(pixel_a, pixel_b);
}



__kernel void median_filter(
        __global uchar* image) {

    int x = get_global_id(0);
    int y = get_global_id(1);
    int width = get_global_size(0) * 2;
    int height = get_global_size(1);

    x += x;
    x += (y + 1) % 2;

    uint pos = (y * width + x) * 3;
    uint3 pixels[4];
    int size = 0;
    
    if (x + 1 < width) {
        pixels[size] = (uint3)(
                image[pos + 3],
                image[pos + 4],
                image[pos + 5]);
        size++;
    }
    if (x - 1 > 0) {
        pixels[size] = (uint3)(
                image[pos - 3],
                image[pos - 2],
                image[pos - 1]);
        size++;
    }
    if (y + 1 < height){
        pixels[size] = (uint3)(
                image[pos + width * 3],
                image[pos + width * 3 + 1],
                image[pos + width * 3 + 2]);
        size++;
    }
    if (y - 1 > 0){
        pixels[size] = (uint3)(
                image[pos - width * 3],
                image[pos - width * 3 + 1],
                image[pos - width * 3 + 2]);
        size++;
    }

    float dist = 0;
    int index = 0;
    for (int i = 1; i < size; i++) {
        dist += get_distance(convert_float3(pixels[0]), convert_float3(pixels[i]));
    }

    for (int i = 1; i < size; i++) {
        float diff_sum = 0;
        for (int j = 1; j < size; j++) {
            if (i != j) {
                diff_sum += get_distance(convert_float3(pixels[i]), convert_float3(pixels[j]));
            }
        }
        if (dist > diff_sum) {
            diff_sum = dist;
            index = i;
        }
    }

    image[pos] = convert_uchar(pixels[index].x);
    image[pos + 1] = convert_uchar(pixels[index].y);
    image[pos + 2] = convert_uchar(pixels[index].z);

}
