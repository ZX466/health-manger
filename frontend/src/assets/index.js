/**
 * 前端静态资源统一管理
 * 图片和音频位于 public/assets/，通过绝对路径引用
 */

const BASE = '/assets'

// ==================== 哈基米（猫咪）图片 ====================
export const hajimiImages = [
  '680bc15901f9fx7I.jpg',
  '680bc2ffb8b36uf2.gif',
  '681a46ece1cd1qft.jpeg',
  '681f86c26f89aviH.jpeg',
  '68222c4b783c1lFZ.jpeg',
  '68222c4bae80cwAQ.jpeg',
  '68222c4cb855becx.jpeg',
  '68222c4df19feHWp.jpeg',
  '68222c4e5733aByW.gif',
  '68222c4f29862DzT.jpeg',
  '68222c4fed80dyse.jpeg',
  '68222c5114272wRK.jpeg',
  '68222c5188be7kWo.jpeg',
  '68222c5615176qt0.jpeg',
  '68222c57a0e4agSD.jpeg',
  '68222c57e52258DI.jpeg',
  '68222c5817caaLov.jpeg',
  '682f249e38eca5PJ.jpg',
  '682fe668f0b2frX2.gif',
  '6830779443b1278N.jpg',
  '68307794ca3d7hdE.png',
  '68307794da14f5Mq.png',
  '6830779528d27K2W.jpg',
  '683876e02dd3098u.png',
  '688117bfd8915jjv.png',
].map(f => `${BASE}/images/hajimi/${f}`)

// ==================== 奶龙 GIF 动图 ====================
export const nailongGifs = [
  'bing_02_v2-77c7ecdd44ab5e3106ea61e738b55f8e_1440w.gif',
  'bing_03_v2-cb260f963307298076d2a6be099fa0f7_1440w.gif',
  'bing_05_v2-2c8cbc4b35fcb8313adee4f79b059971_1440w.gif',
  'bing_09_20210216082626_ZWCNd.gif',
  'bing_10_v2-182199da14f2f8c9fb90a0785ddf4d09_1440w.gif',
  'bing_13_v2-13ec48728b94d1450abdde91c9e05f92_1440w.gif',
  'bing_15_v2-7f2ada495b8d6e4247d0e5c317927ff5_1440w.gif',
  'bing_18_v2-c5f802c39a46f12f3bd083c00a64cb0c_1440w.gif',
  'bing_19_v2-9a70cad278261b992329d7a5cf90f657_1440w.gif',
  'bing_20_20220303113117_3642d.thumb.400_0.gif',
  'bing_21_v2-b6e367b1c9f51aedc385b312db49ad68_1440w.gif',
  'bing_26_v2-6aedf029c1dec8ac022c8d65c3061ed0_1440w.gif',
  'bing_29_20220303112708_afb5b.thumb.400_0.gif',
  'bing_31_v2-b56bff1e2d73ad4302032080e17ceb4a_1440w.gif',
  'bing_40_20220303112710_fe6d6.thumb.400_0.gif',
  'bing_44_v2-2ab1d061f78b8de521e1fd20561b4fd3_1440w.gif',
  'bing_45_20220303112708_afb5b.gif',
  'bing_46_v2-7985ebf18a822c5bdde021aadab80d0c_1440w.gif',
  'bing_47_v2-a8bdc1c15919e4557970ea240f9dfeef_1440w.gif',
  'bing_48_20220303112545_a6c10.thumb.400_0.gif',
  'bing_49_v2-2092d6ed7d7a79b3c88b10c3e25c6fb0_1440w.gif',
  'gif_04_20220303112708_afb5b.thumb.400_0.gif',
  'gif_05_20220303112545_a6c10.thumb.400_0.gif',
  'gif_07_20220303113119_6a9d2.thumb.400_0.gif',
  'gif_08_20220303112710_fe6d6.thumb.400_0.gif',
].map(f => `${BASE}/images/nailong/gif/${f}`)

// ==================== 奶龙表情包 ====================
export const nailongMemes = [
  'bing_07_v2-b4e3f6ad0cbe6f4648b88a8d9741e211_1440w.jpg',
  'bing_08_6750702430334j6k.jpg',
  'bing_11_6949a5f01b9025LH.jpeg',
  'bing_12_v2-2df512e2f54db889c5a2667fd57518b4_r.jpg',
  'bing_14_v2-32ac9676ea87afb95d8fac913cd6d7c0_1440w.jpg',
  'bing_17_v2-0c599ef6f8587fe0559d8512b6f09832_r.jpg',
  'bing_22_w700d1q75cms.jpg',
  'bing_23_6737706c14883XhG.jpg',
  'bing_24_v2-751d3f9fccb15bc9f52f6d279dbb65a5_r.jpg',
  'bing_25_v2-5ebc8a9964702a18227e880e09684d10_1440w.jpg',
  'bing_28_v2-1fdfddfdad4d0fafa714f9bd1b705555_r.jpg',
  'bing_30_6949a5f0394caQ4e.jpeg',
  'bing_32_v2-315cb1525ace5f01a44af4773c9be2a8_r.jpg',
  'bing_35_v2-83a76ac798a1944af2f00daa491f795f_1440w.jpg',
  'bing_36_v2-4d4d9445311930862d3c38a36d1cbd14_r.jpg',
  'bing_37_6949a5ec7621fcFM.jpeg',
  'bing_39_v2-69a76d2d689397267f0cc47945717d4a_1440w.jpg',
  'bing_42_v2-6993b97ab9a240a082d72b7b4a1e2129_r.jpg',
  'bing_43_v2-b6e367b1c9f51aedc385b312db49ad68_r.jpg',
  'img_00_6737706c14883XhG.jpg',
  'img_02_6949a5f01b9025LH.jpeg',
  'img_11_v2-b718d772f1fd54b3c388a30265c97976_r.jpg',
  'img_12_v2-b6234b52b17425626cec33cf0ce18564_1440.gif',
  'img_13_20220303112148_e9ee6.thumb.1000_0.gif',
  'img_15_v2-13ec48728b94d1450abdde91c9e05f92_1440.gif',
].map(f => `${BASE}/images/nailong/memes/${f}`)

// ==================== 奶龙 PNG 素材 ====================
export const nailongPngs = [
  `${BASE}/images/nailong/png/bing_34_B8SV5w57Ul5VLzq.thumb.400_0.jpg`,
  `${BASE}/images/nailong/png/png_09_6b2619b9f1b3440a84cff5a29bbf23f5.png`,
  `${BASE}/images/nailong/nailong_sample1.jpg`,
]

// ==================== 音效 ====================
export const audioClips = {
  bellyLaugh: `${BASE}/audio/cartoon-belly-laugh.mp3`,
  crazyLaugh: `${BASE}/audio/cartoon-crazy-laugh.mp3`,
  giggle: `${BASE}/audio/cartoon-giggle.mp3`,
  pixabayLaugh: `${BASE}/audio/pixabay-cartoon-laugh.mp3`,
  pixabayLaughAlt: `${BASE}/audio/pixabay_cartoon_laugh.mp3`,
}

// ==================== 工具函数 ====================

/** 随机获取一张哈基米图片 */
export function randomHajimi() {
  return hajimiImages[Math.floor(Math.random() * hajimiImages.length)]
}

/** 随机获取一个奶龙 GIF */
export function randomNailongGif() {
  return nailongGifs[Math.floor(Math.random() * nailongGifs.length)]
}

/** 随机获取一张奶龙表情包 */
export function randomNailongMeme() {
  return nailongMemes[Math.floor(Math.random() * nailongMemes.length)]
}
