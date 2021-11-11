---
layout: post
title:  MiniRTS - 03 Selection and input handling
categories: [C#,Unity3D,MiniRTS]

permalink: /:title
---


Most RTS games have more or less the same functionalities when it comes to user input and unit / building selection. In this post I try to tackle both. First we are going to implement the input handling which will allow the player to click on objects in the game. After that we will implement the selection handling which means, selecting single objects or even multiple objects at once by dragging the mouse or double clicking on an object. This is what we are going to have at the end of this post:

![SelectionAndInputHandling result]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_Result.gif)

[You can download the project files from my GitHub repository](https://github.com/Cxyda/MiniRTS-Tutorial/tree/0.1)

## Input handling

For now, the input handling will happen in 2 classes 
- `InputHandler.cs` and 
- `SelectionRectDrawer.cs`

We will create both classes within the `Assets/Scripts/Game/InputHandling` folder.

The *InputHandler* listens to user input and publishes events when an input happens. We don't call other scripts directly here to reduce coupling of the classes and to be able to use this class in other projects as well. That's in general a very good practice.

Create a class called `InputHandler` and implement the `ILateTickable` interface. This interface comes with *Zenject* and adds the `LateTick()` method which is called everytime Unity calls `LateUpdate()` in its `MonoBehaviour` classes. We could also let `InputHandler` inherit from `MonoBehaviour` but then we would need to attach this class to any GameObject in the scene. This can be error prone when we forget to do so and just adds additional stuff which we need to think about. So let's just implement `ILateTickable` and let *Zenject* to the *thinking* for us. 


{% gist ebff8fb6f76213bd0af12c3b19f95b8e InputHandler.cs %}


First we want to know when the player clicks the left mouse button. This ist simple and straight forward. We create a method and check for the mouse button goes up again and we store this information in some variable so that we can use this information later in this class.

{% gist 047ae2809a89db03361935481a6122f8 InputHandler.cs %}


Easy! We also want to support double clicking, at least for the left mouse button. If you also want to support double clicks with right mouse button, feel free to implement it on your own. To check for double clicks we need a timer to track the elapsed time between the first and the second click. If we received a second click within a defined threshold, we consider this as double-click. Otherwise, we reset the timer and check again on the next click.

{% gist 666720531fa4f0ce27da4dd50476947d InputHandler.cs %}


First, we check if a left mouse button click has been performed in this frame. If so, we check whether we already started the double-click timer and if the elapsed time is smaller than the defined threshold. If that's the case we know the user performed a double-click. The reason for that is that we only start the timer when the left mouse button has already been down. Don't be confused why we do this after checking `_leftMouseButtonWasDown` again instead of handling that in the case above. This is necessary to distinguish between the first and the second click. We also need to reset the data when the timer exceeded the threshold. 

The whole class until now looks like this:

{% gist 303ed61ee1165818768e75de5d185f58 InputHandler.cs %}


As you can see I already added the three methods we just wrote to the `LateTick()` method as well as the variables where we store our data. The only thing which is left for now is to reset the data, so we can start fresh on the next frame. To do so, we add a `ResetMouseInputs()` methods at the end of `LateUpdate()` which looks` like this:

{% gist 39acd361f8f56c1449e2ae3e92bd3213 InputHandler.cs %}


To test this script wen need to bind it in our `GameInstaller.cs` class which we created in the last blogpost. Add this line within our `InstallBindings()` method.

{% gist 90fbf931e2fb26967bdb1849fe3d0c3f GameInstaller.cs %}


As you can see we use `BindInterfacesAndSelfTo<T>` to bind our class. This binds the concrete `InputHandler` class. If we would also have implemented an `IInputHandler` interface we would also bind that and we could use that interface instead of the concrete class to reduce coupling even more. `AsSingle()` means that we want to bind it as [Singleton](https://en.wikipedia.org/wiki/Singleton_pattern) which means we will use only one single instance of this in our game. `NonLazy()` tells Zenject that we wan't to create an instance right away, and we don't want to wait until any other class requests a reference to it, before it gets instantiated.

Press the play button and do some left, right and double left-clicks in your game window. you should see **Left click**, **Right click** and **Double left-click** logs printed to the console. Magic!

Currently, we only log text to the console instead of publishing events, but we will fix that now. First, we need to create three events at the top of the class, and we also create a `InvokeEvents()` method which we invoke in the `LateTick()` method right before we call `ResetMouseInputs()`.

{% gist c2faf198d9500178597ee64c6e914705 InputHandler.cs %}


Great work so far! Now other classes can subscribe to the `OnLeftClickPerformed`, `OnDoubleLeftClickPerformed` and `OnRightClickPerformed` events and then get notified when the user performs one of these inputs.

Another very important selection feature of RTS games is the multi selection of objects via mouse-drag. When the user starts to press the left mouse button and moves the cursor, a rectangular area will be drawn to the screen, which selects all objects within this area.

![MouseDrag selection]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_DragSelection.gif)

To do this we create a method called `CheckForMouseDrag()` in the `LateTick()` method **after** we check for our clicks and **before** we invoke the events of course. This method we check whether the left mouse button goes down and stores the mouse position. When the mouse-down position has been set we need to keep track of the mouse movement which updates every frame, to calculate the selection rectangle. When the distance between the mouse-down position and the current mouse position is bigger than a defined threshold we consider the drag as valid. We do this because we don't want to see the selection rectangle appear when we do a mouse click and move the mouse just a tiny bit. I chose a threshold of 10 pixels for now but feel free to choose something different.

{% gist 3a9cf841ad93f0fb6e6f001027ca1322 InputHandler.cs %}


I decided to make the `mouseDownPosition` and `currentMousePosition` of type `Vector3?`. This means it's a *nullable* Vector3 type, which means we can also assign `null` as a value to the positions. This is much better than assigning some arbitrary value which would flag that the position is unset. If you use a nullable type you need to check if a value has been set with the `HasValue()` method and then you can access the value. Otherwise, you could run into a `NullReferenceException` when the value is null. The `GetScreenRect()` method handles the fact that we need to flip the y coordinates in our rectangle calculation because the mouse position is calculated from the *bottom-left*, which is (0/0) where [rectangles in Unity](https://docs.unity3d.com/ScriptReference/Rect.html) start from the *top-left* and go to the *bottom right*.

Since the left mouse-button-up input, when a drag ends, could trigger a left-click or even a left double-click, which we don't want, we need to add a check to the `CheckLeftClick()` and `CheckLeftDoubleClick()` to prevent that. The full code with these changes can be seen in the listing below.

The last important feature we need to implement is that the user should be able to modify a selection. Most RTS games allow this by holding down the *SHIFT* or *CTRL* key on your keyboard. When this key is pressed, a user can add or remove objects from the selection without deselecting the current objects. This is easy, and we only need to check `Input.GetKey(ModifySelectionKey)` on every frame and store the value. See the `CheckForKeyboardInput()` method in the listing below.

{% gist 0372c657d30f85673d9382a510583f9a InputHandler.cs %}


You may have noticed that I sneaked in a small helper method called `IsCursorAboveUi()` which returns whether the mouse cursor is above a UI when a click happens. If that's the case we ignore the click, otherwise we would be able to select Unity which are behind our UI which we obviously don't want.

## Drawing the selection rectangle
The logic for selecting objects with a selection rectangle is working, but we are not drawing this rectangle yet so the player doesn't see it. We have to fix that! We create another class for that called `SelectionRectDrawer` in the `InputHandling` folder. We will draw this rectangle as a `GUI.Box` on the screen using Unity's `OnGUI()` method. There are other ways to do that, but they are more complex and we don't have benefits from using those more complex solutions. To be able to use `OnGUI()` method we unfortunately have to inherit from `MonoBehaviour`. Let's go ahead and create that very simple component.

{% gist e4606bb53480134654232b5f3ccfe4b1 %}


There are not many interesting things going on in this class. The first thing you may have recognized is the `[Inejct]` attribute at the beginning of the class. This attribute is used to tell Zenject that it should inject a reference to the `InputHandler` into this class and store it in the `_inputHandler` using the binding we created earlier. We need to assign a texture to the *DragRectTexture* field in the inspector. For that, use the *./Content/Textures/DragRectTexture.png* texture of the base project.
We also need to create a `GUIStyle` to be able to add [9-sling](https://en.wikipedia.org/wiki/9-slice_scaling) to the texture, otherwise the texture would be scaled across the whole selection rect and would look pretty bad when the user draws a big rectangle. The borders of the 9-slice scaling are set to 4 pixels on each side.
When we receive the `OnSelectionRectChanged` event which gets published by the `InputHandler` class we store the rectangle so that we can draw it in the `OnGUI()` method each frame. When the player releases the mouse button after a drag, the `OnDragEndedEvent` gets published, and we set the rectangle to null so that we don't draw it anymore in the `OnGUI()` method.


## Selection handling
Let's continue with the selection handling. We need three new classes for that.

- `SelectableComponent.cs`
- `SelectionService.cs`
- `CamerRaycastHandler.cs`

Create a new folder in our `Assets/Scripts/Game/` folder called `Selection`. In that folder we will put these three classes. We start with the `SelectableComponent` class.

{% gist a7940bd77ce7f0ac98ffa240981b3640 InputHandler.cs %}

This class inherits from `MonoBehaviour` and will be put on every GameObject that can be selected. We could also use layers for that, but since a GameObject can only be on one layer at a time we gain more flexibility with the component approach. Selected objects in RTS games are normally highlighted with a selection circle around them. There are multiple ways to implement these selection circles.

One common method would be to use a [projector](https://docs.unity3d.com/Manual/class-Projector.html) which projects a texture or a shader on the terrain. The problem with this is that it can get quite expensive when you select a lot of Units because the Terrain gets drawn again for every projector which projects something on it. This can get your graphics card busy quickly. Since we want to have a solid foundation for the next RTS blockbuster we discard this method.

Another option would be to use only a single projector and use some shader magic to draw all selection circles for all selected units at once. As mentioned, this requires shader magic and my shader knowledge is limited, so I can't say anything about this method.

Option 3 would be to create a mesh below the unit and put a texture or shader on it which shows a circle or something similar to highlight that object. Using a texture is super simple and works well when the objects are all of similar size. The problem is when the objects vary in size, the texture would get scaled and the circle would be thicker for big objects and thinner for small ones. We can solve this when using a shader and calculate the circle procedurally instead of using a texture. Another advantage of shaders are that we can do more fancy stuff like merging the outlines together when the circles overlap. As I said earlier, my shader knowledge is limited but luckily we have the internet and there's always someone who's better than you out there. I found [Sander Homan's Blog](http://homans.nhlrebel.com/2011/12/07/remove-overlap-of-circles-with-shaders/) who wrote an article about a shader which does exactly this. Nice! Thanks Sander. We will use this shader as a base. I did some small changes to this shader. I added a tint color to be able to colorize the outline. Additionally, I added a border thickness variable which lets us define the border thickness as we like and I made the shader support same circle thicknesses no matter how big the mesh is which we use, to draw the selection circle. You can see the result in the image below.

![MouseDrag selection]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_SelectionCircles.png)

[The improved shader can be found here](https://github.com/Cxyda/MiniRTS-Tutorial/blob/0b7568d14d4156c097a0a2aa67814cccb8052380/Assets/Content/Shaders/CircleOverlap.shader)

Okay, back to our `SelectableComponent` class from above. We decided to go with a selection mesh which we can turn on and off when we select or deselect the object. We need to create this object in every GameObject prefab which can be selected within our game. If you are using my project files open all the Prefabs in the `Content/Prefabs/` folder and add a new `Quad` mesh to them by right-clicking in the Hierarchy window and selecting `3D Object -> Quad`. Call it for example `SelectionCircle`, assign the `SelectionCircle` Material to it and adjust the size of the quad as you like.

![Selection Circle on a quad mesh]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_SelectionCircleMesh.png)

You should also adjust the *Lighting* and *Probe* settings of the Mesh Renderer component (see screenshot above).

Assign the `SelectableComponent` script the `ModelPlaceholder` GameObject in our prefabs and drag the `SelectionCircle` GameObject to the `SelectionCircleGO` field in the inspector. Repeat this process for all your Prefabs. You can of course also assign the `SelectableComponent` script to any other GameObject in the Prefab which has a collider component. Otherwise our we won't be able to hit the object with our Raycasts (which we will do in the *Casting Rays* section below).

 
The core functionality is already implemented but we add two more methods to optimize our performance. We add the `OnBecameVisible()` and `OnBecameInvisible()` methods to our `SelectableComponent` class. Those methods are `MonoBehaviour` methods and will be called when the renderer of the GameObject becomes visible or invisible to any camera. We can use this behaviour to register and unregister our object to our `SelectionService`.

{% gist e558cb28a27a78d3284482f6049e229d SelectableComponent.cs %}


### The Selection Service

Create a new class called `SelectionService.cs` in the `Scripts/Game/Selection/` folder. This class will be responsible for selecting and deselecting of objects in our game. We start with a `Select()` and a `ClearSelection()` method.

{% gist 22527cf47ac7a42e32e19167b4f53aa8 SelectionService.cs %}


The `Select()` method accepts the `SelectableComponent` as parameter as well as a bool flags whether we want to add the object to our current selection. If we don't want to add the newly selected object to the current selection we first clear the current selection. After that we check if we passed a valid object which we can select and add to our `_selectedEntities` HashSet.

We also need a constructor for this class where we can initialize our HashSet and register for our selection event.

{% gist 945b6b0c720dd3c3046648b569535c67 SelectionService.cs %}


Okay. Sorry if I confused you with this constructor. I'll explain. As you know, we are using Zenject for our dependency injection and Zenject will inject classes, which are bound, into classes it instantiates. Which means Zenject will handle the `camerRaycastHandler` and the `inputHandler` so don't worry about these. The next important thing is that we register to our Selection and Input events we publish in the classes we wrote earlier. When these events happen we call `Select()` and `GetEntitiesWithinSelectionRect()` which we need to implement now.

{% gist 85026e66c6a1ffcee2918619e4603e67 SelectionService.cs %}


In the `GetEntitiesWithinSelectionRect()` method we check if there are objects within the selection rect on the screen when the player draws one. For that we iterate over the `_visibleSelectables` HashSet which contains all objects on Screen. We don't need to worry about units off screen since we cannot select what we can't see.

The `GetScreenPoint()` simply converts the objects position into the screen position using the `WorldToScreenPoint()` method. When we have the screen point we again need to flip the Y coordinates since the calculated position starts from the bottom-left but the selection rect starts from the top-left. After we made sure we set the z-position to 0 we return the position. Afterwards we can call `selectionRect.Value.Contains(screenPoint)` to check if the object is within the selection rect and select it.

You may have noticed that I silently introduced the `_visibleSelectables` HashSet. We iterate over it, but we didn't fill it with objects yet. For that we need the `RegisterSelectable(...)` and `UnregisterSelectable(...)` methods which are already called by the `SelectableComponent`'s `OnBecameVisible()` and `OnBecameInvisible()` methods.

{% gist 59ddfbf3cedf21ac6d58bf8efd9b01d3 SelectionService.cs %}

Great! That's it! Our `SelectionService` is done. The whole class code looks like this:

{% gist 3f54f85fab2c76c1cfc201e97fcf8a5b SelectionService.cs %}


### Casting Rays

The last piece which is missing, is the ability to click on GameObjects which then get selected. Remember we listen for clicks, but we are lacking the information where we click and what's below our cursor. We will implement that now. Create a `CamerRaycastHandler` class and put it in the `Scripts/Selection` folder as well. This class will work closely with our game camera and will cast rays from the camera through our mouse cursor position to distinguish whether we clicked on something.

{% gist 4033010e94970483a735fa6357c20c69 CamerRaycastHandler.cs %}


As you can see we implement Zenject's `IInitializable` interface. This interface has an `Initialize()` which is called when this class gets created basically the same way `Awake()` gets called on `MonoBehaviour` classes. We could also inherit from `MonoBehaviour` and attach it to a GameObject in the scene and assign the camera by hand, but as mentioned earlier this can be forgotten and therefore we let Zenject handle this for us. Zenject also injects a reference to our `InputHandler` class because we used the `[Inject]` attribute. Awesome!

In the `Initialize()` method we register for our click events and call `OnLeftClickPerformed()` and `OnDoubleLeftClickPerformed()` when they happen. Now we need a reference to our GameCamera. We cannot simply assign it like we would if this would be a component on a GameObject so we need to get the reference at the start of the game. We do this by calling `Camera.main`. Everywhere on the internet they say you should avoid this like the plague because what Unity does behind the scenes is it calls `GameObject.FindGameObjectWithTag("MainCamera")` which is expensive especially when you do it in a method which gets called every frame, but here we do it only once at the start and cache the reference so that is fine. 

Now we need to cast rays from the camera through our mouse position and check whether we hit a GameObject (collider) which has a `SelectableComponent` attached.

{% gist 1cd9c67920be2bb7c034fba5a1758312 SelectableComponent.cs %}


The actual ray casting happens in the `TryGetSelectable(...)` method. We create a ray with the `_camera.ScreenPointToRay(Input.mousePosition)` method and do a raycast with `Physics.Raycast(ray, out var hit)`. If our ray hits something, the method returns `true` and stores the result in the `out hit` result. Likewise, the `TryGetSelectable()` method returns `true` when we hit a GameObject with a `SelectableComponent` attached. The object we hit is then stored in the `out selectable` variable and passed back to the caller. 

## The Bindings

Now we only need to bind our `SelectionService` and `CamerRaycastHandler` classes, so that Zenject handles them for us. To do so, go to the `GameInstaller.cs` class and extend the `InstallBindings()` method as followed.

{% gist 8dc1fbd3660887fac3d90d6101b785cc GameInstaller.cs %}


Congratulations! You completed this tutorial. Your *game* is able to select units like all other AAA RTS games out there. We implemented these systems with minimal class coupling. In this tutorial we used the concrete class implementations instead of interfaces to shorten the post and since we only will have one implementation it doesn't really matter. When you check out the project repository you will see that I created and used interfaces because it's a good habit to use interfaces and for very big projects it also gives you a very nice boost in compile times when you separate your interfaces and your concrete implementation into different assembly definition files.

## BONUS: Object grouping

All RTS games support object grouping by holding down the *CTRL* key and pressing number from 1 to 0. Let's add that as well. We need to add some lines to out `InputHandler` class. We extend the `CheckForKeyboardInput()` method a little bit and the `GetSelectionGroupKeypress()` method. We also need to add two new events. `OnSelectionGroupSaved` and `OnSelectionGroupRestored`.  

{% gist b94685a0d3e2d1e78f3f012b2dc0129f GameInstaller.cs %}


That's it already for our `InputHandler` class. We now invoke events when the player presses *CTRL* + \[0..9] to store the current selection or \[0..9] only to load a selection. 

Next we need to extend the `SelectionService` class a little. We need to listen for the two new events we just created. When they happen we need to store or load the current selection. Sounds easy right?

{% gist 9c4b28961a39d001006c3462ea50925b GameInstaller.cs %}


![SelectionAndInputHandling result]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_SelectionGrouping.gif)

The project files of the current state can be found in [my GitHub repository](https://github.com/Cxyda/MiniRTS-Tutorial/tree/0.2).

Next we will look into Building placement and Unit productions!

##### [< Project Setup]({% post_url 2021-10-23-MiniRTS-ProjectSetup %}) | [Building placement >]({% post_url 2021-11-11-MiniRTS-BuildingPlacement %}) >

