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


__kernel void median_filter(
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
