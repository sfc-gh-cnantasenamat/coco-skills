"""Proportional masks, shadows, presenter framing, and transition composition."""
import math
import cv2
import numpy as np


def rounded_mask(width, height, radius):
    radius = min(radius, width/2, height/2)
    vertical, horizontal = np.ogrid[:height, :width]
    distance_x = np.abs(horizontal-(width-1)/2)-(width/2-radius)
    distance_y = np.abs(vertical-(height-1)/2)-(height/2-radius)
    distance = np.hypot(np.maximum(distance_x, 0), np.maximum(distance_y, 0))
    distance += np.minimum(np.maximum(distance_x, distance_y), 0)-radius
    return np.clip(.5-distance, 0, 1).astype(np.float32)


def composite(background, foreground, left, top, mask):
    height, width = background.shape[:2]
    start_x, start_y = max(0, left), max(0, top)
    end_x, end_y = min(width, left+foreground.shape[1]), min(height, top+foreground.shape[0])
    if end_x <= start_x or end_y <= start_y:
        return background
    alpha = mask[start_y-top:end_y-top, start_x-left:end_x-left, None]
    pixels = foreground[start_y-top:end_y-top, start_x-left:end_x-left]
    background[start_y:end_y, start_x:end_x] = pixels*alpha+background[start_y:end_y, start_x:end_x]*(1-alpha)
    return background


def shadow(width, height, mask, left, top):
    scale = height/720
    layer = np.zeros((height, width, 1), np.float32)
    white = np.ones((*mask.shape, 1), np.float32)
    composite(layer, white, left, top+round(7*scale), mask)
    return cv2.GaussianBlur(layer[:, :, 0], (0, 0), 9*scale)[..., None]*.48


class Composer:
    def __init__(self, config, geometry, center_samples=None):
        self.config, self.geometry = config, geometry
        self.center_samples = center_samples
        width, height = geometry['width'], geometry['height']
        style = config['style']
        if style.get('background_image'):
            background = cv2.imread(style['background_image'], cv2.IMREAD_COLOR)
            if background is None:
                raise ValueError('Cannot decode background image')
            # Background is decorative; center-cover rather than distort an arbitrary image.
            ratio = max(width/background.shape[1], height/background.shape[0])
            background = cv2.resize(background, (math.ceil(background.shape[1]*ratio), math.ceil(background.shape[0]*ratio)))
            top, left = (background.shape[0]-height)//2, (background.shape[1]-width)//2
            background = background[top:top+height, left:left+width]
        else:
            vertical, horizontal = np.ogrid[:height, :width]
            blend = (.55*horizontal/(width-1)+.45*vertical/(height-1))[..., None]
            blend = blend**2*(3-2*blend)
            colors = [np.array([int(color[index:index+2], 16) for index in (5, 3, 1)])
                      for color in style['background_colors']]
            background = (colors[0]*(1-blend)+colors[1]*blend).astype(np.uint8)
        self.screen_mask = rounded_mask(geometry['screen_width'], geometry['screen_height'], height*style['corner_radius'])
        self.presenter_corner_radius = style.get('presenter_corner_radius', .5)
        self.circle_mask = rounded_mask(geometry['diameter'], geometry['diameter'],
                                        geometry['diameter']*self.presenter_corner_radius)
        screen_shadow = shadow(width, height, self.screen_mask, geometry['screen_left'], geometry['screen_top'])
        self.background = (background*(1-screen_shadow)).astype(np.uint8)
        self.circle_shadow = shadow(width, height, self.circle_mask, geometry['presenter_left'], geometry['presenter_top'])

    def frame(self, camera, screen, frame_index, fps):
        config, geometry = self.config, self.geometry
        width, height = geometry['width'], geometry['height']
        start, outro, transition = config['tutorial_start'], config['outro_start'], config['transition_frames']
        if frame_index < start-transition or frame_index >= outro+transition:
            return camera
        result = composite(self.background.copy(), screen, geometry['screen_left'], geometry['screen_top'], self.screen_mask)
        center = config['style']['body_center_x']
        if self.center_samples:
            points = np.asarray(self.center_samples)
            center = np.interp(frame_index/fps, points[:, 0], points[:, 1])
        body_center = center*width
        diameter, margin = geometry['diameter'], geometry['margin']
        if start <= frame_index < outro:
            crop_left = round(np.clip(body_center-height/2, 0, width-height))
            foreground = cv2.resize(camera[:, crop_left:crop_left+height], (diameter, diameter), interpolation=cv2.INTER_AREA)
            result = (result*(1-self.circle_shadow)).astype(np.uint8)
            return composite(result, foreground, geometry['presenter_left'], geometry['presenter_top'], self.circle_mask)
        phase = (frame_index-(start-transition))/(transition-1)
        if frame_index >= outro:
            phase = 1-(frame_index-outro)/(transition-1)
        phase = float(np.clip(phase, 0, 1))
        eased = 1-(1-phase)**3
        travel = eased+.018*math.sin(phase*math.pi*4)*math.sin(phase*math.pi)**2
        crop_width = round(width+(height-width)*eased)
        crop_left = round(np.clip((body_center-height/2)*eased, 0, width-crop_width))
        overlay_height = max(diameter-round(8*height/720), round(height+(diameter-height)*travel))
        overlay_width = round(overlay_height*crop_width/height)
        foreground = cv2.resize(camera[:, crop_left:crop_left+crop_width], (overlay_width, overlay_height), interpolation=cv2.INTER_AREA)
        center_x = width/2+(width-margin-diameter/2-width/2)*eased
        center_y = height/2+(height-margin-diameter/2-height/2)*eased-height*.12*math.sin(math.pi*phase)
        left, top = round(center_x-overlay_width/2), round(center_y-overlay_height/2)
        mask = rounded_mask(overlay_width, overlay_height,
                            min(overlay_width, overlay_height)*self.presenter_corner_radius*eased)
        result = (result*(1-shadow(width, height, mask, left, top)*eased)).astype(np.uint8)
        return composite(result, foreground, left, top, mask)