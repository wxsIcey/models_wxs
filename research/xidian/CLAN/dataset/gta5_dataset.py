# Copyright 2023 Xidian University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
import os.path as osp
import numpy as np
import random
import mindspore.dataset as ds
from PIL import Image


class GTA5DataSet():
    def __init__(self, root, list_path, max_iters=None, crop_size=(321, 321), mean=(128, 128, 128), ignore_label=255):
        self.root = root
        self.list_path = list_path
        self.crop_size = crop_size
        self.ignore_label = ignore_label
        self.mean = mean
        # self.mean_bgr = np.array([104.00698793, 116.66876762, 122.67891434])
        self.img_ids = [i_id.strip() for i_id in open(list_path)]
        if not max_iters == None:
            self.img_ids = self.img_ids * int(np.ceil(float(max_iters) / len(self.img_ids)))
            self.img_ids = self.img_ids[:max_iters]

        self.files = []

        self.id_to_trainid = {7: 0, 8: 1, 11: 2, 12: 3, 13: 4, 17: 5,
                              19: 6, 20: 7, 21: 8, 22: 9, 23: 10, 24: 11, 25: 12,
                              26: 13, 27: 14, 28: 15, 31: 16, 32: 17, 33: 18}
        self.name_temp = ''

        # for split in ["train", "trainval", "val"]:
        for name in self.img_ids:
            img_file = osp.join(self.root, "images/%s" % name)
            label_file = osp.join(self.root, "labels/%s" % name)
            self.files.append({
                "img": img_file,
                "label": label_file,
                "name": name
            })

    def __len__(self):
        return len(self.files)

    def __getitem__(self, index):
        datafiles = self.files[index]

        try:
            image = Image.open(datafiles["img"]).convert('RGB')
            label = Image.open(datafiles["label"])
            name = datafiles["name"]

            # resize
            image = image.resize(self.crop_size,resample=Image.BILINEAR)
            label = label.resize(self.crop_size,resample=Image.NEAREST)

            image = np.asarray(image, np.float32)
            label = np.asarray(label, np.float32)

            # re-assign labels to match the format of Cityscapes
            label_copy = 255 * np.ones(label.shape, dtype=np.float32)
            for k, v in self.id_to_trainid.items():
                label_copy[label == k] = v

            size = image.shape

            image = image[:, :, ::-1]  # change to BGR
            image -= self.mean
            image = image.transpose((2, 0, 1))

        except Exception as e:
            print(f'data processing error: {e}')
            index = index - 1 if index > 0 else index + 1
            return self.__getitem__(index)
        
        return image.copy(), label_copy.copy(), np.array(size)


if __name__ == '__main__':
    dataset_generator = GTA5DataSet("/media/data2/xidian/data/GTA5/",
                                    '/media/data3/hy/CLAN/dataset/gta5_list/train.txt')
    data = iter(dataset_generator).__next__()
    #print(data)
    dataset = ds.GeneratorDataset(dataset_generator, column_names=['image', 'label', 'size'], shuffle=False)

    dataset = dataset.batch(batch_size=1)
    class_set = set()

    for i, data in enumerate(dataset.create_dict_iterator()):
        # 检查数据是否为None
        if data is None:
            print(f"在第{i}个数据点处发现空数据")
            continue  # 或者可以选择退出循环，例如使用break

        image, label, size = data['image'], data['label'], data['size']

        # 检查image, label, size是否为空或异常
        if image is None or label is None or size is None:
            print(f"在第{i}个数据点处发现缺失的数据项")
            continue  # 或者可以选择退出循环，例如使用break

        if image.shape == () or label.shape == () or size.shape == ():
            print(f"在第{i}个数据点处发现异常的数据形状")
            continue  # 或者可以选择退出循环，例如使用break

        #print(image.shape, label.shape)

        list1 = list(label.astype('int32').flatten().asnumpy())
        #print(set(list1))
        class_set = class_set | set(list1)

        # if i == 50:
        #     print(len(class_set), class_set)
        #     break


