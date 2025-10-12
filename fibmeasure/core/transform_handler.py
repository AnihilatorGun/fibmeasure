from .vtransforms import VRichardsonLucyDeconv, VBinarize, VOpening, VCCSFilter, VSkeletonizeEDT, VLineFittingTLS


class TransformHandler:
    transforms = [VRichardsonLucyDeconv(), VBinarize(), VOpening(), VCCSFilter(), VSkeletonizeEDT(), VLineFittingTLS()]

    def __init__(self, source_image):
        self.source_image = source_image
        self.current_transform_idx = 0

        self.transform_result_nodes = {idx: None for idx in range(len(self.transforms))}

    def update_param(self, name, value):
        # Cached node results invalidation
        for idx in range(self.current_transform_idx, len(self.transforms)):
            self.transform_result_nodes[idx] = None

        self.transforms[self.current_transform_idx].set_current_value(name, value)

    @property
    def current_transform_name(self):
        return self.transforms[self.current_transform_idx].transform_name
    
    @property
    def current_transform_annotation(self):
        return self.transforms[self.current_transform_idx].transform_annotation

    def next(self):
        if self.current_transform_idx == len(self.transforms) - 1:
            return False

        self.current_transform_idx += 1
        return True

    def prev(self):
        if self.current_transform_idx == 0:
            return False

        self.current_transform_idx -= 1
        return True

    def get_result_node(self, transform_idx):
        if transform_idx == -1:
            result_node = {'image': self.source_image}
        else:
            result_node = self.transform_result_nodes[transform_idx]

        if result_node is None:
            prev_result_node = self.get_result_node(transform_idx - 1)
            result_node = self.transforms[transform_idx](prev_result_node)
            self.transform_result_nodes[transform_idx] = result_node

        return result_node

    def get_result_image(self, transform_idx):
        if transform_idx == -1:
            return self.source_image

        result_node = self.get_result_node(transform_idx)
        visualization_key = self.transforms[transform_idx].visualization_key

        return result_node[visualization_key]

    def get_before_after_images(self):
        return self.get_result_image(self.current_transform_idx - 1), self.get_result_image(self.current_transform_idx)

    def get_sliders(self):
        return self.transforms[self.current_transform_idx].get_sliders()
