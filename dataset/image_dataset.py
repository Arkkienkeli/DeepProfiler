import numpy as np

import dataset.pixels as px
import dataset.utils as u


class ImageDataset():
    def __init__(self, metadata, category, channels, dataRoot, keyGen):
        self.meta = metadata  # Metadata object with a valid dataframe
        self.category = category  # Column in the metadata that has category labels
        self.channels = channels  # List of column names corresponding to each channel file
        self.root = dataRoot  # Path to the directory of images
        self.keyGen = keyGen  # Function that returns the image key given its record in the metadata
        self.pixelProcessor = px.PixelProcessor()
        self.labels = self.meta.data[self.category].unique()

    def getImagePaths(self, r):
        key = self.keyGen(r)
        image = [self.root + '/' + r[ch] for ch in self.channels]
        return (key, image)

    def sampleImages(self, categ, nImgCat):
        keys = []
        images = []
        labels = []
        for c in categ:
            mask = self.meta.train[self.category] == c
            rec = self.meta.train[mask].sample(n=nImgCat, replace=True)
            for i, r in rec.iterrows():
                key, image = self.getImagePaths(r)
                keys.append(key)
                images.append(image)
                labels.append(c)
        return keys, images, labels

    def getTrainBatch(self, N):
        s = u.tic()
        # Batch size is N
        categ = self.labels.copy()
        # 1. Sample categories
        if len(categ) > N:
            np.random.shuffle(categ)
            categ = categ[0:N]
        # 2. Define images per category
        nImgCat = int(N / len(categ))
        residual = N % len(categ)
        # 3. Select images per category
        keys, images, labels = self.sampleImages(categ, nImgCat)
        if residual > 0:
            np.random.shuffle(categ)
            rk, ri, rl = self.sampleImages(categ[0:residual], 1)
            keys += rk
            images += ri
            labels += rl
        # 4. Open images
        batch = {'keys': keys, 'images': [], 'labels': labels}
        for img in images:
            batch['images'].append(px.openImage(img, self.pixelProcessor))
        u.toc('Loading batch', s)
        return batch

    def scan(self, f, frame='train'):
        if frame == 'all':
            frame = self.meta.data.iterrows()
        elif frame == 'val':
            frame = self.meta.val.iterrows()
        else:
            frame = self.meta.train.iterrows()

        images = [(i, self.getImagePaths(r), r) for i, r in frame]
        for img in images:
            index = img[0]
            image = px.openImage(img[1][1], self.pixelProcessor)
            meta = img[2]
            f(index, image, meta)
        return

    def numberOfRecords(self, dataset):
        if dataset == 'all':
            return len(self.meta.data)
        elif dataset == 'val':
            return len(self.meta.val)
        elif dataset == 'train':
            return len(self.meta.train)
        else:
            return 0
