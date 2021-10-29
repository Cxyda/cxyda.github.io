---
layout: post
title:  MiniRTS - 03 Selection and input handling
categories: [C#,Unity3D,MiniRTS]

permalink: /:title
---


Most RTS games have more or less the same functionalities when it comes to user input and unit / building selection. In this post I try to tackle both. First we are going to implement the input handling which will allow the player to click on objects in the game. After that we will implement the selection handling which means, selecting single objects or even multiple objects at once by dragging the mouse or double clicking on an object. This is what we are going to have at the end of this post:

![SelectionAndInputHandling result]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_Result.gif)

[Get the project files]([You can download the project files from my GitHub repository](https://github.com/Cxyda/MiniRTS-Tutorial/releases/tag/0.1))

## Input handling

For now, the input handling will happen in 2 classes 
- `InputHandler.cs` and 
- `SelectionRectDrawer.cs`

We will create both classes within the `Assets/Scripts/Game/InputHandling` folder.

The *InputHandler* listens to user input and publishes events when an input happens. We don't call other scripts directly here to reduce coupling of the classes and to be able to use this class in other projects as well. That's in general a very good practice.

Create a class called `InputHandler` and implement the `ILateTickable` interface. This interface comes with *Zenject* and adds the `LateTick()` method which is called everytime Unity calls `LateUpdate()` in its `Monobehaviour` classes. We could also let `InputHandler` inherit from `Monobehaviour` but then we would need to attach this class to any GameObject in the scene. This can be error prone when we forget to do so and just adds additional stuff which we need to think about. So let's just implement `ILateTickable` and let *Zenject* to the *thinking* for us. 

```csharp
namespace Game.InputHandling
{
    public class InputHandler : ILateTickable
    {
        public void LateUpdate()
        {
            // more to come
        }
    }
}
```

First we want to know when the player clicks the left mouse button. This ist simple and straight forward. We create a method and check for the mouse button goes up again and we store this information in some variable so that we can use this information later in this class.

```csharp
private void CheckLeftClick()
{
    if (Input.GetMouseButtonUp(0))
    {
        _leftMouseButtonClickPerformed = true;
    }
}
private void CheckRightClick()
{
    if (Input.GetMouseButtonUp(1))
    {
        _rightMouseButtonClickPerformed = true;
    }
}
```
Easy! We also want to support double clicking, at least for the left mouse button. If you also want to support double clicks with right mouse button, feel free to implement it on your own. To check for double clicks we need a timer to track the elapsed time between the first and the second click. If we received a second click within a defined threshold, we consider this as double-click. Otherwise, we reset the timer and check again on the next click.

```csharp
private void CheckLeftDoubleClick()
{
    if (_leftMouseButtonClickPerformed)
    {
        // When the timer is already running and the timer is below the threshold, the user performed a double-click
        if (_doubleClickTimer > 0f && _doubleClickTimer <= DoubleClickThreshold)
        {
            // we need to reset our data to listen for the next double click
            _leftMouseButtonDoubleClickPerformed = true;
            _doubleClickTimer = 0f;
        }
    }
    if (_leftMouseButtonWasDown)
    {
        // increase the timer. When the mouse button goes down the first time, the _doubleClickTimer is equal to 0f
        _doubleClickTimer += Time.deltaTime;
    }
    
    if (_doubleClickTimer > DoubleClickThreshold)
    {
        // Time since the last click exceeded the threshold -> Reset the timer
        _doubleClickTimer = 0f;
        _leftMouseButtonWasDown = false;
    }
}
```

First, we check if a left mouse button click has been performed in this frame. If so, we check whether we already started the double-click timer and if the elapsed time is smaller than the defined threshold. If that's the case we know the user performed a double-click. The reason for that is that we only start the timer when the left mouse button has already been down. Don't be confused why we do this after checking `_leftMouseButtonWasDown` again instead of handling that in the case above. This is necessary to distinguish between the first and the second click. We also need to reset the data when the timer exceeded the threshold. 

The whole class until know looks like this:

```csharp
using UnityEngine;
namespace Game.InputHandling
{
    public class InputHandler : ILateTickable
    {
        // TODO: make these customizable
        /// <summary>
        /// The time in seconds which may elapse at max between 2 clicks to consider it a double-click
        /// </summary>
        private const float DoubleClickThreshold = 0.5f;
    
        private bool _leftMouseButtonClickPerformed;
        private bool _rightMouseButtonClickPerformed;
    
        private float _doubleClickTimer;
        private bool _leftMouseButtonDoubleClickPerformed;
    
        private bool _leftMouseButtonWasDown;
    
        public void LateUpdate()
        {
            CheckLeftClick();
            CheckLeftDoubleClick();
    
            CheckRightClick();
        }
        private void CheckLeftClick()
        {
            if (Input.GetMouseButtonUp(0))
            {
                Debug.Log("Left click");
                _leftMouseButtonClickPerformed = true;
                _leftMouseButtonWasDown = true;
            }
        }
        private void CheckRightClick()
        {
            if (Input.GetMouseButtonUp(1))
            {
                Debug.Log("Right click");
                _rightMouseButtonClickPerformed = true;
            }
        }
        private void CheckLeftDoubleClick()
        {
            if (_leftMouseButtonClickPerformed)
            {
                // When the timer is already running and the timer is below the threshold, the user performed a double-click
                if (_doubleClickTimer > 0f && _doubleClickTimer <= DoubleClickThreshold)
                {
                    Debug.Log("Double Left-click");
                    // we need to reset our data to listen for the next double click
                    _leftMouseButtonDoubleClickPerformed = true;
                    _doubleClickTimer = 0f;
                }
            }
            if (_leftMouseButtonWasDown)
            {
                // increase the timer. When the mouse button goes down the first time, the _doubleClickTimer is equal to 0f
                _doubleClickTimer += Time.deltaTime;
            }
            
            if (_doubleClickTimer > DoubleClickThreshold)
            {
                // Time since the last click exceeded the threshold -> Reset the timer
                _doubleClickTimer = 0f;
                _leftMouseButtonWasDown = false;
            }
        }
    }
}
```

As you can see I already added the three methods we just wrote to the `LateUpdate()` method as well as the variables where we store our data. The only thing which is left for now is to reset the data, so we can start fresh on the next frame. To do so, we add a `ResetMouseInputs()` methods at the end of `LateUpdate()` which looks` like this:

```csharp
    public void LateUpdate()
    {
        CheckLeftClick();
        CheckRightClick();
        CheckLeftDoubleClick();

        ResetMouseInputs();
    }
    //... more code is here
    private void ResetMouseInputs()
    {
        _leftMouseButtonDoubleClickPerformed = false;
        _leftMouseButtonClickPerformed = false;
        _rightMouseButtonClickPerformed = false;
    }
```

To test this script wen need to bind it in our `GameInstaller.cs` class which we created in the last blogpost. Add this line within our `InstallBindings()` method.

```csharp
public override void InstallBindings()
{
    Container.BindInterfacesAndSelfTo<InputHandler>().AsSingle().NonLazy();
}
```

As you can see we use `BindInterfacesAndSelfTo<T>` to bind our class. This binds the concrete `InputHandler` class. If we would also have implemented an `IInputHandler` interface we would also bind that and we could use that interface instead of the concrete class to reduce coupling even more. `AsSingle()` means that we want to bind it as [Singleton](https://en.wikipedia.org/wiki/Singleton_pattern) which means we will use only one single instance of this in our game. `NonLazy()` tells Zenject that we wan't to create an instance right away, and we don't want to wait until any other class requests a reference to it, before it gets instantiated.

Press the play button and do some left, right and double left-clicks in your game window. you should see **Left click**, **Right click** and **Double left-click** logs printed to the console. Magic!

Currently, we only log text to the console instead of publishing events, but we will fix that now. First, we need to create three events at the top of the class, and we also create a `InvokeEvents()` method which we invoke in the `LateTick()` method right before we call `ResetMouseInputs()`.

```csharp
public class InputHandler : ILateTickable
{
    public event Action OnLeftClickPerformed; 
    public event Action OnDoubleLeftClickPerformed;

    public event Action OnRightClickPerformed;

    public void LateUpdate()
    {
        CheckLeftClick();
        CheckLeftDoubleClick();
        CheckRightClick();
        
        InvokeEvents();
        ResetMouseInputs();
    }

    // ... 
    // more class code got omitted here
    // ...

    private void InvokeEvents()
    {
        if (_leftMouseButtonClickPerformed)
        {
            OnLeftClickPerformed?.Invoke();
        }
        if (_leftMouseButtonDoubleClickPerformed)
        {
            OnDoubleLeftClickPerformed?.Invoke();
        }
        if (_rightMouseButtonClickPerformed)
        {
            OnRightClickPerformed?.Invoke();
        }
    }
}
```


Great work so far! Now other classes can subscribe to the `OnLeftClickPerformed`, `OnDoubleLeftClickPerformed` and `OnRightClickPerformed` events and then get notified when the user performs one of these inputs.

Another very important selection feature of RTS games is the multi selection of objects via mouse-drag. When the user starts to press the left mouse button and moves the cursor, a rectangular area will be drawn to the screen, which selects all objects within this area.

![MouseDrag selection]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_DragSelection.gif)

To do this we create a method called `CheckForMouseDrag()` in the `LateTick()` method **after** we check for our clicks and **before** we invoke the events of course. This method we check whether the left mouse button goes down and stores the mouse position. When the mouse-down position has been set we need to keep track of the mouse movement which updates every frame, to calculate the selection rectangle. When the distance between the mouse-down position and the current mouse position is bigger than a defined threshold we consider the drag as valid. We do this because we don't want to see the selection rectangle appear when we do a mouse click and move the mouse just a tiny bit. I chose a threshold of 10 pixels for now but feel free to choose something different.

```csharp
private void CheckForMouseDrag()
{
    if (Input.GetMouseButtonDown(0))
    {
        _mouseDownPosition = Input.mousePosition;
    }

    if (_mouseDownPosition.HasValue)
    {
        _lastFrameMousePosition = _currentMousePosition;
        _currentMousePosition = Input.mousePosition;
    }

    if (_mouseDownPosition.HasValue && _currentMousePosition.HasValue)
    {
        // Calculate the distance of those positions so that we can skip this if the rectanle is too small
        var distance = Vector3.Distance(_mouseDownPosition.Value, _currentMousePosition.Value);
        // DragRectThreshold is a arbitrary value that defines the minimum size of the rectangle
        _isDragging = distance >= DragRectThreshold;
        if (_isDragging)
        {
            _lastDragRect = GetScreenRect(_mouseDownPosition.Value, _currentMousePosition.Value);
        }
    }
    else
    {
        _isDragging = false;
    }
    // If the mouse button goes up, we need to end the drag
    if (Input.GetMouseButtonUp(0))
    {
        _mouseDownPosition = null;
        _currentMousePosition = null;
        _lastFrameMousePosition = null;
        _isDragging = false;
        _lastDragRect = null;
        OnDragEndedEvent?.Invoke();
    }
}
private Rect GetScreenRect(Vector3 screenPosition1, Vector3 screenPosition2)
{
    // Move origin from bottom left to top left
    screenPosition1.y = Screen.height - screenPosition1.y;
    screenPosition2.y = Screen.height - screenPosition2.y;
    // Calculate corners
    var topLeft = Vector3.Min(screenPosition1, screenPosition2);
    var bottomRight = Vector3.Max(screenPosition1, screenPosition2);
    // Create Rect
    return Rect.MinMaxRect(topLeft.x, topLeft.y, bottomRight.x, bottomRight.y);
}
// ... 
// more class code got omitted here
// ...
private void InvokeEvents()
{
    if (_leftMouseButtonClickPerformed)
    {
        OnLeftClickPerformed?.Invoke();
    }
    if (_leftMouseButtonDoubleClickPerformed)
    {
        OnDoubleLeftClickPerformed?.Invoke();
    }
    if (_rightMouseButtonClickPerformed)
    {
        OnRightClickPerformed?.Invoke();
    }
    if (_isDragging && _lastFrameMousePosition != _currentMousePosition)
    {
        OnSelectionRectChanged?.Invoke(_lastDragRect);
    }
}
```

I decided to make the `mouseDownPosition` and `currentMousePosition` of type `Vector3?`. This means it's a *nullable* Vector3 type, which means we can also assign `null` as a value to the positions. This is much better than assigning some arbitrary value which would flag that the position is unset. If you use a nullable type you need to check if a value has been set with the `HasValue()` method and then you can access the value. Otherwise, you could run into a `NullReferenceException` when the value is null. The `GetScreenRect()` method handles the fact that we need to flip the y coordinates in our rectangle calculation because the mouse position is calculated from the *bottom-left*, which is (0/0) where [rectangles in Unity](https://docs.unity3d.com/ScriptReference/Rect.html) start from the *top-left* and go to the *bottom right*.

Since the left mouse-button-up input, when a drag ends, could trigger a left-click or even a left double-click, which we don't want, we need to add a check to the `CheckLeftClick()` and `CheckLeftDoubleClick()` to prevent that. The full code with these changes can be seen in the listing below.

The last important feature we need to implement is that the user should be able to modify a selection. Most RTS games allow this by holding down the *SHIFT* or *CTRL* key on your keyboard. When this key is pressed, a user can add or remove objects from the selection without deselecting the current objects. This is easy, and we only need to check `Input.GetKey(ModifySelectionKey)` on every frame and store the value. See the `CheckForKeyboardInput()` method in the listing below.

```csharp
using System;
using UnityEngine;
using UnityEngine.EventSystems;
using Zenject;

namespace Game.InputHandling
{
    /// <summary>
    /// This component handles mainly the mouse input of the player
    /// It checks for single left and right mouse button clicks as well as double left button clicks and invokes events
    /// when they happen.
    /// </summary>

    public class InputHandler : IInputHandler, ILateTickable
    {
        // TODO: make these customizable
        /// <summary>
        /// The time in seconds which may elapse at max between 2 clicks to consider it a double-click
        /// </summary>
        private const float DoubleClickThreshold = 0.5f;
        /// <summary>
        /// KeyCode of the modify selection key. Should be customised later via the GameControl settings
        /// </summary>
        private const KeyCode ModifySelectionKey = KeyCode.LeftShift;
    
        /// <summary>
        /// The distance in pixels which the user needs to overcome with the mouse button held down before we consider it a 'drag'
        /// </summary>
        private const float DragRectThreshold = 10;
        public event Action OnLeftClickPerformed; 
        public event Action OnDoubleLeftClickPerformed;
    
        public event Action OnRightClickPerformed;
        public event Action<Rect?> OnSelectionRectChanged;
        public event Action OnDragEndedEvent;
    
        /// <summary>
        /// When this is true the current selection will be added to the previous selection, otherwise the selection will be replaced
        /// </summary>
        public bool ModifySelection => _isModifySelectionKeyPressed;
        // has the key been pressed this frame?
        private bool _isModifySelectionKeyPressed = false;
        
        private bool _leftMouseButtonClickPerformed;
        private bool _rightMouseButtonClickPerformed;
    
        private float _doubleClickTimer;
        private bool _leftMouseButtonDoubleClickPerformed;
    
        private bool _leftMouseButtonWasDown;
        private Vector3? _mouseDownPosition;
        private Vector3? _currentMousePosition;
        private bool _isDragging;
        private Vector3? _lastFrameMousePosition;
        private Rect? _lastDragRect;
    
        public void LateTick()
        {
            CheckForKeyboardInput();
    
            CheckLeftClick();
            CheckLeftDoubleClick();
            CheckRightClick();
    
            // Order here is important. Check for MouseDrags only after checking for LeftMouseClicks
            CheckForMouseDrag();
    
            if (_rightMouseButtonClickPerformed)
            {
                // TODO: Check if hit is terrain to give a move command
            }
    
            InvokeEvents();
            ResetMouseInputs();
        }
    
        private void InvokeEvents()
        {
            if (_leftMouseButtonClickPerformed)
            {
                OnLeftClickPerformed?.Invoke();
            }
            if (_leftMouseButtonDoubleClickPerformed)
            {
                OnDoubleLeftClickPerformed?.Invoke();
            }
            if (_rightMouseButtonClickPerformed)
            {
                OnRightClickPerformed?.Invoke();
            }
            if (_isDragging && _lastFrameMousePosition != _currentMousePosition)
            {
                OnSelectionRectChanged?.Invoke(_lastDragRect);
            }
        }
    
        private void ResetMouseInputs()
        {
            _leftMouseButtonDoubleClickPerformed = false;
            _leftMouseButtonClickPerformed = false;
            _rightMouseButtonClickPerformed = false;
        }
    
        private void CheckForKeyboardInput()
        {
            _isModifySelectionKeyPressed = Input.GetKey(ModifySelectionKey);
        }
    
        private void CheckForMouseDrag()
        {
            if (Input.GetMouseButtonDown(0))
            {
                _mouseDownPosition = Input.mousePosition;
            }
    
            if (_mouseDownPosition.HasValue)
            {
                _lastFrameMousePosition = _currentMousePosition;
                _currentMousePosition = Input.mousePosition;
            }
    
            if (_mouseDownPosition.HasValue && _currentMousePosition.HasValue)
            {
                // Calculate the distance of those positions so that we can skip this if the rectanle is too small
                var distance = Vector3.Distance(_mouseDownPosition.Value, _currentMousePosition.Value);
                // DragRectThreshold is a arbitrary value that defines the minimum size of the rectangle
                _isDragging = distance >= DragRectThreshold;
                if (_isDragging)
                {
                    _lastDragRect = GetScreenRect(_mouseDownPosition.Value, _currentMousePosition.Value);
                }
            }
            else
            {
                _isDragging = false;
            }
            // If the mouse button goes up, we need to end the drag
            if (Input.GetMouseButtonUp(0))
            {
                _mouseDownPosition = null;
                _currentMousePosition = null;
                _lastFrameMousePosition = null;
                _isDragging = false;
                _lastDragRect = null;
                OnDragEndedEvent?.Invoke();
            }
        }
        private Rect GetScreenRect(Vector3 screenPosition1, Vector3 screenPosition2)
        {
            // Move origin from bottom left to top left
            screenPosition1.y = Screen.height - screenPosition1.y;
            screenPosition2.y = Screen.height - screenPosition2.y;
            // Calculate corners
            var topLeft = Vector3.Min(screenPosition1, screenPosition2);
            var bottomRight = Vector3.Max(screenPosition1, screenPosition2);
            // Create Rect
            return Rect.MinMaxRect(topLeft.x, topLeft.y, bottomRight.x, bottomRight.y);
        }
    
        private void CheckLeftClick()
        {
            if (!_isDragging && Input.GetMouseButtonUp(0) && !IsCursorAboveUi())
            {
                _leftMouseButtonClickPerformed = true;
                _leftMouseButtonWasDown = true;
            }
        }
    
        private void CheckRightClick()
        {
            if (Input.GetMouseButtonUp(1) && !IsCursorAboveUi())
            {
                _rightMouseButtonClickPerformed = true;
            }
        }
    
        private void CheckLeftDoubleClick()
        {
            if (!_isDragging && _leftMouseButtonClickPerformed)
            {
                // When the timer is already running and the timer is below the threshold, the user performed a double-click
                if (_doubleClickTimer > 0f && _doubleClickTimer <= DoubleClickThreshold)
                {
                    // we need to reset our data to listen for the next double click
                    _leftMouseButtonDoubleClickPerformed = true;
                    _doubleClickTimer = 0f;
                }
            }
            if (_leftMouseButtonWasDown)
            {
                // increase the timer. When the mouse button goes down the first time, the _doubleClickTimer is equal to 0f
                _doubleClickTimer += Time.deltaTime;
            }
            
            if (_doubleClickTimer > DoubleClickThreshold)
            {
                // Time since the last click exceeded the threshold -> Reset the timer
                _doubleClickTimer = 0f;
                _leftMouseButtonWasDown = false;
            }
        }
        
        private static bool IsCursorAboveUi()
        {
            // Check whether the cursor is above a UI GameObject because we want to prevent clicking through UI
            return EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
        }
    }
}
```

You may have noticed that I sneaked in a small helper method called `IsCursorAboveUi()` which returns whether the mouse cursor is above a UI when a click happens. If that's the case we ignore the click, otherwise we would be able to select Unity which are behind our UI which we obviously don't want.

## Drawing the selection rectangle
The logic for selecting objects with a selection rectangle is working, but we are not drawing this rectangle yet so the player doesn't see it. We have to fix that! We create another class for that called `SelectionRectDrawer` in the `InputHandling` folder. We will draw this rectangle as a `GUI.Box` on the screen using Unity's `OnGUI()` method. There are other ways to do that, but they are more complex and we don't have benefits from using those more complex solutions. To be able to use `OnGUI()` method we unfortunately have to inherit from `Monobehaviour`. Let's go ahead and create that very simple component.

```csharp
using Game.InputHandling;
using UnityEngine;
using Zenject;

namespace Game.Selection
{
    /// <summary>
    /// This class handles the drawing of the a selection rectangle when the player drags the mouse across the screen
    /// </summary>
    public class SelectionRectDrawer : MonoBehaviour
    {
        // We use Zenject to inject the InputHandler class
        [Inject] private InputHandler _inputHandler;
    
        [Tooltip("The texture of the selection rect")]
        public Texture2D DragRectTexture;
        
        private Rect? _rect;
        private GUIStyle _dragRectStyle;
    
        private void Awake()
        {
            // register for the OnSelectionRectChanged event and call UpdateSelectionRect() when it happens
            _inputHandler.OnSelectionRectChanged += UpdateSelectionRect;
            _inputHandler.OnDragEndedEvent += ResetRect;
    
            _dragRectStyle = new GUIStyle("box")
            {
                normal =
                {
                    // assign the rect texture
                    background = DragRectTexture
                },
                // define 9-slicing borders
                border = new RectOffset(4, 4, 4, 4)
            };
        }
        private void UpdateSelectionRect(Rect? dragRect)
        {
            _rect = dragRect;
        }
        private void OnGUI()
        {
            if (_rect != null)
            {
                GUI.Box(_rect.Value, "", _dragRectStyle);
            }
        }
        private void ResetRect()
        {
            // reset the rectangle every frame to not draw the texture on the next frame anymore when the player has stopped dragging
            _rect = null;
        }
    }
}
```

There are not many interesting things going on in this class. The first thing you may have recognized is the `[Inejct]` attribute at the beginning of the class. This attribute is used to tell Zenject that it should inject a reference to the `InputHandler` into this class and store it in the `_inputHandler` using the binding we created earlier. We need to assign a texture to the *DragRectTexture* field in the inspector. For that, use the *./Content/Textures/DragRectTexture.png* texture of the base project.
We also need to create a `GUIStyle` to be able to add [9-sling](https://en.wikipedia.org/wiki/9-slice_scaling) to the texture, otherwise the texture would be scaled across the whole selection rect and would look pretty bad when the user draws a big rectangle. The borders of the 9-slice scaling are set to 4 pixels on each side.
When we receive the `OnSelectionRectChanged` event which gets published by the `InputHandler` class we store the rectangle so that we can draw it in the `OnGUI()` method each frame. When the player releases the mouse button after a drag, the `OnDragEndedEvent` gets published, and we set the rectangle to null so that we don't draw it anymore in the `OnGUI()` method.


## Selection handling
Let's continue with the selection handling. We need three new classes for that.

- `SelectableComponent.cs`
- `SelectionService.cs`
- `SelectableRaycastComponent.cs`

Create a new folder in our `Assets/Scripts/Game/` folder called `Selection`. In that folder we will put these three classes. We start with the `SelectableComponent` class.

```csharp
using UnityEngine;
using Zenject;

namespace Game.Selection
{
	/// <summary>
	/// This class can be added to GameObjects that can be selected by the player within the game
	/// </summary>
	public class SelectableComponent : MonoBehaviour
	{
		[Inject] private ISelectionService _selectionService;

		// Will be assigned in the Unity Inspector
		[SerializeField] private GameObject SelectionCircleGO;
		[SerializeField] private bool _isSelected;

		public bool IsSelected => _isSelected;

		public void Select(bool select)
		{
			_isSelected = select;
			SelectionCircleGO.SetActive(_isSelected);
		}
	}
}
```

This class inherits from `Monobehaviour` and will be put on every GameObject that can be selected. We could also use layers for that, but since a GameObject can only be on one layer at a time we gain more flexibility with the component approach. Selected objects in RTS games are normally highlighted with a selection circle around them. There are multiple ways to implement these selection circles.

One common method would be to use a [projector](https://docs.unity3d.com/Manual/class-Projector.html) which projects a texture or a shader on the terrain. The problem with this is that it can get quite expensive when you select a lot of Units because the Terrain gets drawn again for every projector which projects something on it. This can get your graphics card busy quickly. Since we want to have a solid foundation for the next RTS blockbuster we discard this method.

Another option would be to use only a single projector and use some shader magic to draw all selection circles for all selected units at once. As mentioned, this requires shader magic and my shader knowledge is limited, so I can't say anything about this method.

Option 3 would be to create a mesh below the unit and put a texture or shader on it which shows a circle or something similar to highlight that object. Using a texture is super simple and works well when the objects are all of similar size. The problem is when the objects vary in size, the texture would get scaled and the circle would be thicker for big objects and thinner for small ones. We can solve this when using a shader and calculate the circle procedurally instead of using a texture. Another advantage of shaders are that we can do more fancy stuff like merging the outlines together when the circles overlap. As I said earlier, my shader knowledge is limited but luckily we have the internet and there's always someone who's better than you out there. I found [Sander Homan's Blog](http://homans.nhlrebel.com/2011/12/07/remove-overlap-of-circles-with-shaders/) who wrote an article about a shader which does exactly this. Nice! Thanks Sander. We will use this shader as a base. I did some small changes to this shader. I added a tint color to be able to colorize the outline. Additionally, I added a border thickness variable which lets us define the border thickness as we like and I made the shader support same circle thicknesses no matter how big the mesh is which we use, to draw the selection circle. You can see the result in the image below.

![MouseDrag selection]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_SelectionCircles.png)

[The improved shader can be found here](https://github.com/Cxyda/MiniRTS-Tutorial/blob/0b7568d14d4156c097a0a2aa67814cccb8052380/Assets/Content/Shaders/CircleOverlap.shader)

Okay, back to our `SelectableComponent` class from above. We decided to go with a selection mesh which we can turn on and off when we select or deselect the object. We need to create this object in every GameObject prefab which can be selected within our game. If you are using my project files open all the Prefabs in the `Content/Prefabs/` folder and add a new `Quad` mesh to them by right-clicking in the Hierarchy window and selecting `3D Object -> Quad`. Call it for example `SelectionCircle`, assign the `SelectionCircle` Material to it and adjust the size of the quad as you like.

![Selection Circle on a quad mesh]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_SelectionCircleMesh.png)

You should also adjust the *Lighting* and *Probe* settings of the Mesh Renderer component (see screenshot above).

Assign the `SelectableComponent` script the `ModelPlaceholder` GameObject in our prefabs and drag the `SelectionCircle` GameObject to the `SelectionCircleGO` field in the inspector. Repeat this process for all your Prefabs. You can of course also assign the `SelectableComponent` script to any other GameObject in the Prefab which has a collider component. Otherwise our we won't be able to hit the object with our Raycasts (which we will do in the *Casting Rays* section below).

 
The core functionality is already implemented but we add two more methods to optimize our performance. We add the `OnBecameVisible()` and `OnBecameInvisible()` methods to our `SelectableComponent` class. Those methods are `Monobehaviour` methods and will be called when the renderer of the GameObject becomes visible or invisible to any camera. We can use this behaviour to register and unregister our object to our `SelectionService`.

```csharp
public class SelectableComponent : MonoBehaviour
{
    [Inject] private ISelectionService _selectionService;

    // ... 
    // more class code got omitted here
    // ...

    private bool _isVisible;

    private void OnBecameVisible()
    {
        _isVisible = true;
        _selectionService.RegisterSelectable(this);
    }
    private void OnBecameInvisible()
    {
        _isVisible = false;
        // If the object is selected, don't unregister it, otherwise the SelectionService would lose it.
        if (!_isSelected)
        {
            _selectionService.UnregisterSelectable(this);
        }
    }
}
```

### The Selection Service

Create a new class called `SelectionService.cs` in the `Scripts/Game/Selection/` folder. This class will be responsible for selecting and deselecting of objects in our game. We start with a `Select()` and a `ClearSelection()` method.

```csharp
namespace Game.Selection
{
	public class SelectionService
	{
		private readonly HashSet<SelectableComponent> _selectedEntities;

		public void Select(SelectableComponent selectable, bool addToSelection = false, bool selectAllOfSameType = false)
		{
			if (!addToSelection)
			{
				ClearSelection();
			}

			if (selectable == null) return;

			// Handle the special case when we want to modify a selection and click on an already selected object.
			if (addToSelection)
			{
				selectable.Select(false);
				_selectedEntities.Remove(selectable);
			}
			else
			{
				selectable.Select(true);
				_selectedEntities.Add(selectable);
			}
            //TODO: Add functionality to select all objects of the same type on screen
		}

		private void ClearSelection()
		{
			foreach (var selectedEntity in _selectedEntities)
			{
				selectedEntity.Select(false);
			}
			_selectedEntities.Clear();
		}
    }
}
```

The `Select()` method accepts the `SelectableComponent` as parameter as well as a bool flags whether we want to add the object to our current selection. If we don't want to add the newly selected object to the current selection we first clear the current selection. After that we check if we passed a valid object which we can select and add to our `_selectedEntities` HashSet.

We also need a constructor for this class where we can initialize our HashSet and register for our selection event.

```csharp
public class SelectionService : ISelectionService
{
    private readonly HashSet<SelectableComponent> _selectedEntities;
	private readonly HashSet<SelectableComponent> _visibleSelectables;
    private readonly InputHandler _inputHandler;
    private readonly Camera _camera;

    public SelectionService(SelectableRaycastComponent selectableRaycastComponent, InputHandler inputHandler)
    {
        // Initialize our HashSets
        _selectedEntities = new HashSet<SelectableComponent>();
        _visibleSelectables = new HashSet<SelectableComponent>();

        _inputHandler = inputHandler;

        // Register for our Input and Selection events
        _inputHandler.OnSelectionRectChanged += GetEntitiesWithinSelectionRect;
        selectableRaycastComponent.OnSelectionPerformedEvent += Select;

        _camera = Camera.main;
    }

// ... 
// more class code got omitted here
// ...
}
```

Okay. Sorry if I confused you with this constructor. I'll explain. As you know, we are using Zenject for our dependency injection and Zenject will inject classes, which are bound, into classes it instantiates. Which means Zenject will handle the `selectableRaycastComponent` and the `inputHandler` so don't worry about these. The next important thing is that we register to our Selection and Input events we publish in the classes we wrote earlier. When these events happen we call `Select()` and `GetEntitiesWithinSelectionRect()` which we need to implement now.

```csharp
private void GetEntitiesWithinSelectionRect(Rect? selectionRect)
{
    // Again first check whether we want to add the objects to our current selection
    if (!_inputHandler.ModifySelection)
    {
        ClearSelection();
    }
    // If the rect is null, just return
    if (!selectionRect.HasValue)
    {
        return;
    }
    // check all objects stored in the _visibleSelectables if their positions are within the selection rect
    foreach (var selectable in _visibleSelectables)
    {
        var screenPoint = GetScreenPoint(selectable);
        if (selectionRect.Value.Contains(screenPoint))
        {
            Select(selectable, true, false);
        }
    }
}
private Vector3 GetScreenPoint(SelectableComponent selectable)
{
    var screenPoint = _camera.WorldToScreenPoint(selectable.transform.position);
    // Move origin from bottom left to top left
    screenPoint.y = Screen.height - screenPoint.y;
    // reset z-coordinate just to be sure
    screenPoint.z = 0;
    return screenPoint;
}
``` 

In the `GetEntitiesWithinSelectionRect()` method we check if there are objects within the selection rect on the screen when the player draws one. For that we iterate over the `_visibleSelectables` HashSet which contains all objects on Screen. We don't need to worry about units off screen since we cannot select what we can't see.

The `GetScreenPoint()` simply converts the objects position into the screen position using the `WorldToScreenPoint()` method. When we have the screen point we again need to flip the Y coordinates since the calculated position starts from the bottom-left but the selection rect starts from the top-left. After we made sure we set the z-position to 0 we return the position. Afterwards we can call `selectionRect.Value.Contains(screenPoint)` to check if the object is within the selection rect and select it.

You may have noticed that I silently introduced the `_visibleSelectables` HashSet. We iterate over it, but we didn't fill it with objects yet. For that we need the `RegisterSelectable(...)` and `UnregisterSelectable(...)` methods which are already called by the `SelectableComponent`'s `OnBecameVisible()` and `OnBecameInvisible()` methods.

```csharp
public void RegisterSelectable(SelectableComponent selectableComponent)
{
    _visibleSelectables.Add(selectableComponent);
}

public void UnregisterSelectable(SelectableComponent selectableComponent)
{
    _visibleSelectables.Remove(selectableComponent);
}
```

Great! That's it! Our `SelectionService` is done. The whole class code looks like this:

```csharp
using System.Collections.Generic;
using Game.InputHandling;
using UnityEngine;

namespace Game.Selection
{
	/// <summary>
	/// This class handles the selection of <see cref="SelectableComponent"/> entities.
	/// </summary>
	public interface ISelectionService
	{
		void Select(SelectableComponent selectable, bool addToSelection = false, bool selectAllOfSameType = false);

		void RegisterSelectable(SelectableComponent selectableComponent);
		void UnregisterSelectable(SelectableComponent selectableComponent);
	}

	public class SelectionService : ISelectionService
	{
		private readonly HashSet<SelectableComponent> _selectedEntities;
		private readonly HashSet<SelectableComponent> _visibleSelectables;
		private readonly InputHandler _inputHandler;
		private readonly Camera _camera;

		public SelectionService(SelectableRaycastComponent selectableRaycastComponent, InputHandler inputHandler)
		{
			// Initialize our HashSets
			_selectedEntities = new HashSet<SelectableComponent>();
			_visibleSelectables = new HashSet<SelectableComponent>();

			_inputHandler = inputHandler;

			_inputHandler.OnSelectionRectChanged += GetEntitiesWithinSelectionRect;
			selectableRaycastComponent.OnSelectionPerformedEvent += Select;

			_camera = Camera.main;
		}
		public void Select(SelectableComponent selectable, bool addToSelection = false, bool selectAllOfSameType = false)
		{
			if (!addToSelection) ClearSelection();
			if (selectable == null) return;

			// Handle the special case when we want to modify a selection and click on an already selected object.
			if (addToSelection && _selectedEntities.Contains(selectable))
			{
				selectable.Select(false);
				_selectedEntities.Remove(selectable);
			}
			else
			{
				selectable.Select(true);
				_selectedEntities.Add(selectable);
			}
            //TODO: Add functionality to select all objects of the same type on screen
		}
		private void GetEntitiesWithinSelectionRect(Rect? selectionRect)
		{
			if (!_inputHandler.ModifySelection)
			{
				ClearSelection();
			}
			// If the rect is null, just return
			if (!selectionRect.HasValue)
			{
				return;
			}
			// check all objects stored in the _visibleSelectables if their positions are within the selection rect
			foreach (var selectable in _visibleSelectables)
			{
				var screenPoint = GetScreenPoint(selectable);
				if (selectionRect.Value.Contains(screenPoint))
				{
					Select(selectable, true, false);
				}
			}
		}
		private Vector3 GetScreenPoint(SelectableComponent selectable)
		{
			var screenPoint = _camera.WorldToScreenPoint(selectable.transform.position);
			// Move origin from bottom left to top left
			screenPoint.y = Screen.height - screenPoint.y;
			// reset z-coordinate just to be sure
			screenPoint.z = 0;
			return screenPoint;
		}
		public void RegisterSelectable(SelectableComponent selectableComponent)
		{
			_visibleSelectables.Add(selectableComponent);
		}
		public void UnregisterSelectable(SelectableComponent selectableComponent)
		{
			_visibleSelectables.Remove(selectableComponent);
		}
		private void ClearSelection()
		{
			foreach (var selectedEntity in _selectedEntities)
			{
				selectedEntity.Select(false);
			}
			_selectedEntities.Clear();
		}
	}
}
```


### Casting Rays

The last piece which is missing, is the ability to click on GameObjects which then get selected. Remember we listen for clicks, but we are lacking the information where we click and what's below our cursor. We will implement that now. Create a `SelectableRaycastComponent` class and put it in the `Scripts/Selection` folder as well. This class will work closely with our game camera and will cast rays from the camera through our mouse cursor position to distinguish whether we clicked on something.

```csharp
using System;
using Game.InputHandling;
using UnityEngine;
using Zenject;
namespace Game.Selection
{
	/// <summary>
	/// This class casts rays from the camera through the mouse position to check whether we clicked on an object
	/// with a <see cref="SelectableComponent"/> attached.
	/// </summary>
	public class SelectableRaycastComponent : IInitializable
	{
		private Camera _camera;
		[Inject] private IInputHandler _inputHandler;
		
		public void Initialize()
		{
			_inputHandler.OnLeftClickPerformed += OnLeftClickPerformed;
			_inputHandler.OnDoubleLeftClickPerformed += OnDoubleLeftClickPerformed;
			_camera = Camera.main;
		}

		private void OnLeftClickPerformed()
		{
		}
		private void OnDoubleLeftClickPerformed()
		{
		}
    }
}

```

As you can see we implement Zenject's `IInitializable` interface. This interface has an `Initialize()` which is called when this class gets created basically the same way `Awake()` gets called on `Monobehaviour` classes. We could also inherit from `Monobehaviour` and attach it to a GameObject in the scene and assign the camera by hand, but as mentioned earlier this can be forgotten and therefore we let Zenject handle this for us. Zenject also injects a reference to our `InputHandler` class because we used the `[Inject]` attribute. Awesome!

In the `Initialize()` method we register for our click events and call `OnLeftClickPerformed()` and `OnDoubleLeftClickPerformed()` when they happen. Now we need a reference to our GameCamera. We cannot simply assign it like we would if this would be a component on a GameObject so we need to get the reference at the start of the game. We do this by calling `Camera.main`. Everywhere on the internet they say you should avoid this like the plague because what Unity does behind the scenes is it calls `GameObject.FindGameObjectWithTag("MainCamera")` which is expensive especially when you do it in a method which gets called every frame, but here we do it only once at the start and cache the reference so that is fine. 

Now we need to cast rays from the camera through our mouse position and check whether we hit a GameObject (collider) which has a `SelectableComponent` attached.

```csharp
private void OnLeftClickPerformed()
{
    if (TryGetSelectable(out var selectable))
    {
        // Invoke the event passing the selectable, whether the user presses the ModifySelection key and whether we want
        // to select all all objects of the same type as well
        OnSelectionPerformedEvent?.Invoke(selectable, _inputHandler.ModifySelection, false);
    }
    else
    {
        // In this case we didn't click on a selectable object so pass null and clear the selection
        OnSelectionPerformedEvent?.Invoke(null, false, false);
    }
}
private void OnDoubleLeftClickPerformed()
{
    if (TryGetSelectable(out var selectable))
    {
        // Most RTS games support double clicking on an object selects all objects of the same type.
        // Therefore we pass `true` as third parameter
        OnSelectionPerformedEvent?.Invoke(selectable, _inputHandler.ModifySelection, true);
    }
}
private bool TryGetSelectable(out SelectableComponent selectable)
{
    var ray = _camera.ScreenPointToRay(Input.mousePosition);
    selectable = null;
    if (!Physics.Raycast(ray, out var hit))
    {
        return false;
    }
    // We did hit a Collider. Check if the gameObject has a SelectableComponent attached
    selectable = hit.transform.GetComponent<SelectableComponent>();
    return selectable != null;
}
```

The actual ray casting happens in the `TryGetSelectable(...)` method. We create a ray with the `_camera.ScreenPointToRay(Input.mousePosition)` method and do a raycast with `Physics.Raycast(ray, out var hit)`. If our ray hits something, the method returns `true` and stores the result in the `out hit` result. Likewise, the `TryGetSelectable()` method returns `true` when we hit a GameObject with a `SelectableComponent` attached. The object we hit is then stored in the `out selectable` variable and passed back to the caller. 

## The Bindings

Now we only need to bind our `SelectionService` and `SelectableRaycastComponent` classes, so that Zenject handles them for us. To do so, go to the `GameInstaller.cs` class and extend the `InstallBindings()` method as followed.

```csharp
// within the GameInstaller class
public override void InstallBindings()
{
    Container.BindInterfacesAndSelfTo<InputHandler>().AsSingle();
    Container.BindInterfacesAndSelfTo<SelectionService>().AsSingle().NonLazy();
    Container.BindInterfacesAndSelfTo<SelectableRaycastComponent>().AsSingle().NonLazy();
}
```

Congratulations! You completed this tutorial. Your *game* is able to select units like all other AAA RTS games out there. We implemented these systems with minimal class coupling. In this tutorial we used the concrete class implementations instead of interfaces to shorten the post and since we only will have one implementation it doesn't really matter. When you check out the project repository you will see that I created and used interfaces because it's a good habit to use interfaces and for very big projects it also gives you a very nice boost in compile times when you separate your interfaces and your concrete implementation into different assembly definition files.

## BONUS: Object grouping

All RTS games support object grouping by holding down the *CTRL* key and pressing number from 1 to 0. Let's add that as well. We need to add some lines to out `InputHandler` class. We extend the `CheckForKeyboardInput()` method a little bit and the `GetSelectionGroupKeypress()` method. We also need to add two new events. `OnSelectionGroupSaved` and `OnSelectionGroupRestored`.  

```csharp
// within the InputHandler class

private const KeyCode SaveSelectionGroupKey = KeyCode.LeftControl;

// Add 2 new events at the top of the class 
public event Action<byte> OnSelectionGroupSaved;
public event Action<byte> OnSelectionGroupRestored;

// ... 
// more class code got omitted here
// ...

private void CheckForKeyboardInput()
{
    _isModifySelectionKeyPressed = Input.GetKey(ModifySelectionKey);

    var groupId = GetSelectionGroupKeypress();
    if (groupId >= 0 && Input.GetKey(SaveSelectionGroupKey))
    {
        OnSelectionGroupSaved?.Invoke((byte)groupId);
    }
    else if (groupId >= 0)
    {
        OnSelectionGroupRestored?.Invoke((byte)groupId);
    }
}
// This method returns the key index when a number key has been pressed on the keyboard. Or -1 if not
private static sbyte GetSelectionGroupKeypress()
{
    sbyte groupId = -1;
    if (Input.GetKeyDown(KeyCode.Alpha0)) groupId = 0;
    else if (Input.GetKeyDown(KeyCode.Alpha1)) groupId = 1;
    else if (Input.GetKeyDown(KeyCode.Alpha2)) groupId = 2;
    else if (Input.GetKeyDown(KeyCode.Alpha3)) groupId = 3;
    else if (Input.GetKeyDown(KeyCode.Alpha4)) groupId = 4;
    else if (Input.GetKeyDown(KeyCode.Alpha5)) groupId = 5;
    else if (Input.GetKeyDown(KeyCode.Alpha6)) groupId = 6;
    else if (Input.GetKeyDown(KeyCode.Alpha7)) groupId = 7;
    else if (Input.GetKeyDown(KeyCode.Alpha8)) groupId = 8;
    else if (Input.GetKeyDown(KeyCode.Alpha9)) groupId = 9;
    return groupId;
}
```

That's it already for our `InputHandler` class. We now invoke events when the player presses *CTRL* + \[0..9] to store the current selection or \[0..9] only to load a selection. 

Next we need to extend the `SelectionService` class a little. We need to listen for the two new events we just created. When they happen we need to store or load the current selection. Sounds easy right?

```csharp
// within the SelectionService class

private readonly HashSet<SelectableComponent>[] _selectionGroups;

// We need to extend the constructor a little so that it looks like this:
public SelectionService(SelectableRaycastComponent selectableRaycastComponent, InputHandler inputHandler)
{
    // Initialize our HashSets
    _selectedEntities = new HashSet<SelectableComponent>();
    _visibleSelectables = new HashSet<SelectableComponent>();

    _selectionGroups = new HashSet<SelectableComponent>[10];    // We need to initialize our new selecttionGroups array
    _inputHandler = inputHandler;

    _inputHandler.OnSelectionRectChanged += GetEntitiesWithinSelectionRect;
    _inputHandler.OnSelectionGroupSaved += SaveSelection;           // Register for the new event
    _inputHandler.OnSelectionGroupRestored += RestoreSelection;     // Register for the new event
    selectableRaycastComponent.OnSelectionPerformedEvent += Select;

    _camera = Camera.main;
}
// ... 
// more class code got omitted here
// ...

private void SaveSelection(byte selectionGroupIndex)
{
    if(selectionGroupIndex >= _selectionGroups.Length) return;
    // Get the selection HashSet or create a new one if it's null
    var selection = _selectionGroups[selectionGroupIndex] ?? new HashSet<SelectableComponent>();

    selection.Clear();
    // Iterate over _selectedEntities and add the entities one by one instead of assigning it directly,
    // otherwise we would assign the reference to the HashSet instead of its values
    foreach (var selectedEntity in _selectedEntities)
    {
        selection.Add(selectedEntity);
    }
    _selectionGroups[selectionGroupIndex] = selection;
}
private void RestoreSelection(byte selectionGroupIndex)
{
    if(selectionGroupIndex >= _selectionGroups.Length) return;
    var selection = _selectionGroups[selectionGroupIndex];
    if(selection == null) return;
    if(!_inputHandler.ModifySelection) ClearSelection();

    foreach (var selectedEntity in selection)
    {
        Select(selectedEntity, true);
    }
}
```

![SelectionAndInputHandling result]({{site.baseurl}}/images/resources/MiniRTS_series/SelectionAndInputHandling_SelectionGrouping.gif)

The project files of the current state can be found in [my GitHub repository](https://github.com/Cxyda/MiniRTS-Tutorial/tree/0.2).

Next we will look into Building placement and Unit productions!

##### [< Project Setup]({% post_url 2021-10-23-MiniRTS-ProjectSetup %}) | Building placement and factories >

