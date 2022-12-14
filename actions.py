import bpy
from . import config
from . import keyframes


def getNextSwapId():
    intIndex = 0
    for obj in bpy.data.objects:
        intId = obj.get("key_id")
        if intId is not None and intId > intIndex:
            intIndex = intId
    return intIndex+1


def getNextSwapObjectId(obj):
    intSwapObjectId = keyframes.getKeyframeValue(
        obj, '["key_object_id"]', 0, 'max')
    if intSwapObjectId is None:
        return 0
    return intSwapObjectId+1


def setSwapKey(obj, intObjectId, intFrame, update=True):
    if update == True:
        obj['key_object_id'] = intObjectId
    if obj.animation_data is None:
        obj.keyframe_insert(
            data_path='["key_object_id"]', frame=intFrame)
    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.data_path == '["key_object_id"]':
            fcurve.keyframe_points.insert(frame=intFrame, value=intObjectId)
            for keyframe_point in fcurve.keyframe_points:
                keyframe_point.interpolation = 'CONSTANT'


def getSwapObjectName(intSwapId, intSwapObjectId):
    # container/placeholder id + frame created
    # frame created doesn't need to be the only frame used. you can copy and past the key to reuse
    if intSwapId is not None and intSwapObjectId is not None:
        return f'{config.PREFIX}_{intSwapId}_{intSwapObjectId}'


def getObject(strName):
    for obj in bpy.data.objects:
        if obj.name_full == strName:
            return obj
    return None


def getObjectCopy(obj):
    if obj is not None:
        objNew = obj.copy()
        objNew.data = obj.data.copy()
        if obj.animation_data is not None and obj.animation_data.action is not None:
            objNew.animation_data.action = obj.animation_data.action.copy()
        if obj.data.animation_data is not None and obj.data.animation_data.action is not None:
            objNew.data.animation_data.action = obj.data.animation_data.action.copy()
        return objNew


def swapData(objTarget, objReference):
    objTarget.data = objReference.data
    if objReference.animation_data is not None:
        objTarget.animation_data = objReference.animation_data
    objTarget["key_object"] = objReference.name_full


def getFrameObject(obj, intObjectId):
    if intObjectId is not None:
        strSwapObject = getSwapObjectName(obj.get("key_id"), intObjectId)
        objFrame = getObject(strSwapObject)
        if objFrame is not None:
            return objFrame
    return None


def getTmp(objTarget):
    intSwapId = objTarget.get("key_id")
    if intSwapId is not None:
        strTmp = f'{config.PREFIX}_{intSwapId}_tmp'
        objTmp = getObject(strTmp)
        if objTmp is not None:
            return objTmp
        else:
            return setTmp(intSwapId, objTarget)


def setTmp(objTarget):
    intSwapId = objTarget.get("key_id")
    strTmp = f'{config.PREFIX}_{intSwapId}_tmp'
    objTmp = getObject(strTmp)
    if objTmp is not None:
        # get the old data block so we can remove it
        objDataBlock = objTmp.data
        objTmp.data = objTarget.data.copy()
        if objTmp.type == 'CURVE':
            bpy.data.curves.remove(objDataBlock)
        elif objTmp.type == 'MESH':
            bpy.data.meshes.remove(objDataBlock)
    else:
        objTmp = bpy.data.objects.new(strTmp, objTarget.data.copy())
        objTmp.data.use_fake_user = True
        objTmp["key_id"] = intSwapId
    return objTmp


def onFrame(scene):
    context = bpy.context
    strMode = 'OBJECT'
    if context.active_object is not None:
        strMode = context.object.mode
    # object swapping for key feature
    if strMode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in scene.objects:
        # obj must have an id and set an object_id it expects
        # obj must have same id as swa object and not already by the one in use
        # intObjectId = obj.get("key_object_id")
        objTmp = getTmp(obj)
        intObjectId = keyframes.getKeyframeValue(
            obj, '["key_object_id"]', scene.frame_current, '<=')
        if intObjectId is not None:
            objFrame = getFrameObject(obj, intObjectId)
            if objFrame is not None and obj.get("key_object") != objFrame.name_full:
                # override tmp data block
                swapData(obj, objFrame)
                objTmp = setTmp(objFrame)
                swapData(obj, objTmp)

    if strMode == 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')


def getSwapId(obj):
    # get the ID for the OBJECT group (not the frame/mesh)
    intSwapId = obj.get('key_id')
    if intSwapId is None:
        intSwapId = getNextSwapId()
        obj['key_id'] = intSwapId
    # set a tmp object if none exists
    strTmp = f'{config.PREFIX}_{intSwapId}_tmp'
    objTmp = getObject(strTmp)
    if objTmp is None:
        objTmp = bpy.data.objects.new(strTmp, obj.data.copy())
        objTmp.data.use_fake_user = True
        objTmp["key_id"] = intSwapId
    return intSwapId


def getSwapObjectId(obj, intFrame):
    intSwapObjectId = keyframes.getKeyframeValue(
        obj, '["key_object_id"]', intFrame, '=')
    if intSwapObjectId is None:
        intSwapObjectId = getNextSwapObjectId(obj)
    return intSwapObjectId


def removeGeo(obj):
    if obj.type == 'CURVE':
        for i, spline in enumerate(obj.data.splines):
            try:
                obj.data.splines.remove(spline)
            except:
                pass
    elif obj.type == 'MESH':
        for i, vert in enumerate(obj.data.vertices):
            try:
                obj.data.vertices.remove(vert)
            except:
                pass


def setFrameObject(obj, strFrame, intSwapId):
    objFrame = getObject(strFrame)
    if objFrame is None:
        # print('no frame object found', strFrame)
        # create the frame object
        objFrame = bpy.data.objects.new(strFrame, obj.data.copy())
        objFrame.data.use_fake_user = True
        objFrame["key_id"] = intSwapId
    else:
        objFrame.data = obj.data.copy()
    # if obj.animation_data is not None and hasattr(obj.animation_data, 'copy'):
    #    objFrame.animation_data = obj.animation_data.copy()
    if obj.data.animation_data is not None and hasattr(obj.data.animation_data, 'copy'):
        objFrame.data.animation_data = obj.data.animation_data.copy()


def setSwapObject(context, obj, intFrame):
    strMode = context.object.mode
    if strMode == 'EDIT':
        obj.update_from_editmode()
    if hasattr(context, 'active_object') == False:
        context.view_layer.objects.active = obj
    intSwapId = getSwapId(obj)
    intSwapObjectId = getSwapObjectId(obj, intFrame)
    strFrame = getSwapObjectName(obj.get("key_id"), intSwapObjectId)
    obj["key_object"] = strFrame
    # make sure a frame object doesn't already exist
    setFrameObject(obj, strFrame, intSwapId)
    setSwapKey(obj, intSwapObjectId, intFrame)
    bpy.app.handlers.frame_change_post.clear()
    bpy.app.handlers.frame_change_post.append(onFrame)


# take all selected objects, and assign them to active object as keyframes from current position
def addSwapObjects(context, arrSelected, obj):
    intSwapId = getSwapId(obj)
    intCurrentFrame = context.scene.frame_current
    for i, objSelected in enumerate(arrSelected):
        intInsertFrame = intCurrentFrame+i
        keyframes.nudgeFrames(obj, intInsertFrame, 1)
        intSwapObjectId = getSwapObjectId(obj, intInsertFrame)
        # get the frame object name based on the target object
        strFrame = getSwapObjectName(obj.get("key_id"), intSwapObjectId)
        # but the objects being copied are the selected ones
        setFrameObject(objSelected, strFrame, intSwapId)
        # set swap key, but dont change current key, because we are nudging frames not changing frames
        setSwapKey(obj, intSwapObjectId, intInsertFrame, update=False)


def removeObject(obj):
    bpy.data.objects.remove(obj)
    strType = obj.type
    if strType == 'CURVE':
        bpy.data.curves.remove(obj.data)
    elif strType == 'MESH':
        bpy.data.meshes.remove(obj.data)


def redraw(arrAreas=[]):
    # redraw(['DOPESHEET_EDITOR', 'GRAPH_EDITOR'])
    for area in bpy.context.screen.areas:
        if len(arrAreas) == 0 or area.type in arrAreas:
            for region in area.regions:
                region.tag_redraw()


def remove_keys(obj):
    keyframes.removeKeyframes(obj, '["key_object_id"]')
    redraw(['DOPESHEET_EDITOR', 'GRAPH_EDITOR'])
    return


def insert_blank(obj, intFrame):
    print('not sure what to do here, BLANK is not a keyframe concept?')


def clone_key(context, obj, intFrame):
    # Push keyframes to make room for duplicate
    keyframes.nudgeFrames(obj, intFrame+1, 1)
    # get current key
    intSwapObjectId = keyframes.getKeyframeValue(
        obj, '["key_object_id"]', intFrame, '=')
    if intSwapObjectId is not None:
        # Duplicate key in next frame
        setSwapKey(obj, intSwapObjectId, intFrame+1, update=False)


def clone_unique_key(context, obj, intFrame):
    # Push keyframes to make room for duplicate
    keyframes.nudgeFrames(obj, intFrame+1, 1)
    # get the current frame object
    intSwapObjectId = keyframes.getKeyframeValue(
        obj, '["key_object_id"]', intFrame, '=')
    strFrameObject = getSwapObjectName(obj.get("key_id"), intSwapObjectId)
    objFrame = getObject(strFrameObject)
    # copy the current frame object to a new one
    addSwapObjects(context, [objFrame], obj)
    return


def clone_object(context, obj):
    # copy the primary object
    objNew = getObjectCopy(obj)
    objNew['key_id'] = None
    # change the swap id
    setSwapObject(context, objNew, context.scene.frame_current)
    objCollection = obj.users_collection[0]
    objCollection.objects.link(objNew)
    # copy all of the frames associated, using the new swap id, but SAME frame object id
    intSwapId = getSwapId(objNew)
    arrFrames = keyframes.getFrames(obj, '["key_object_id"]', -1, '>')
    arrFrames = list(set(arrFrames))
    for intFrame in arrFrames:
        intFrame = int(intFrame)
        # get the frame IDs
        objFrame = getObject(getSwapObjectName(getSwapId(obj), intFrame))
        if objFrame:
            objNewFrame = getObjectCopy(objFrame)
            objNewFrame.name = getSwapObjectName(intSwapId, intFrame)
            objNewFrame['key_id'] = intSwapId
    return


def setCollection(strCollection):
    if strCollection in bpy.data.collections:
        setCollection(f'{strCollection}_KEYS')
    else:
        return bpy.data.collections.new(name=strCollection)


def add_asset(obj):
    # get a list of the the objects
    arrFrames = keyframes.getSelectedFrames(obj, '["key_object_id"]', 'y')
    arrFrames = list(set(arrFrames))
    # set the collection as an asset .asset_mark()
    for intFrame in arrFrames:
        intFrame = int(intFrame)
        strFrameObject = getSwapObjectName(obj.get("key_id"), intFrame)
        objFrame = getObject(strFrameObject)
        if objFrame:
            objFrame.asset_mark()
            objFrame.asset_generate_preview()


def exposeSelectedFrameObjects(obj, remove=False):
    # unselect the parent object
    obj.select_set(False)
    objCollection = obj.users_collection[0]
    # get the selected keyframes array
    arrKeyframes = keyframes.getSelectedFrames(obj, '["key_object_id"]', 'x')
    for intFrame in arrKeyframes:
        intFrame = int(intFrame)
        # get the object for that keyframe
        intSwapObjectId = keyframes.getKeyframeValue(
            obj, '["key_object_id"]', intFrame, '=')
        strFrameObject = getSwapObjectName(obj.get("key_id"), intSwapObjectId)
        objFrame = getObject(strFrameObject)
        # link the object to the same collection as parent
        if objFrame is not None:
            strFrameName = f'{obj.name}_Frame_{intFrame}'
            if remove == True:
                objFrame.name = strFrameName
                objCollection.objects.link(objFrame)
                objFrame['key_id'] = None
                # leave the new object as selected.
                objFrame.select_set(True)
                # remove keyframes from old object
                keyframes.actKeyframe(obj, intFrame, 'remove')
            elif remove == False:
                # make a copy
                objNew = bpy.data.objects.new(
                    strFrameName, objFrame.data.copy())
                objCollection.objects.link(objNew)
                objNew.select_set(True)
