---
layout: post
title:  MiniRTS - 04 Building Placement
categories: [C#,Unity3D,MiniRTS]
---

Welcome back! Today we want to tackle another very important part of most RTS games. Base building! Some people might
 argue that base building is outdated for RTS games, but I'm still a big fan of te classics like Warcraft, Age of
  Empires or Company of Heroes, so I will add this as well. Placing buildings is actually quite simple but if you
   have flexibility, extendability and clean architecture in mind there is a lot to do. So let's get started. At the
    end of this section you will have something like this:

![SelectionAndInputHandling result]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_Result.gif)

[You can download the project files from my GitHub repository](https://github.com/Cxyda/MiniRTS-Tutorial/tree/0.2)

### First, add the Addressables package
We will also add some infrastructure like asset loading to our game which will make our lives easier later on. For
 that, we will use Addressables. We are also going to add a very small piece of simulation code. First, we need to
  add the Addressables package. For that, go to the Unity package manager: `Window -> Package Manager` and add the
   `Addressables` package from the *Unity Registry* to the game. The latest version for me of this package is `1.16.19`.

![Addressables package in the package manager]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_PackageManager.png)


After importing the new package we are ready to use Addressables in our game. If you are unfamiliar with Addressables
, and my explanations in this tutorial are not enough, I'd recommend asking google for some basic resources. Since we
 are using assembly definition files we also need to add a reference to the addressables package to our Game assembly
 . Let's find and select the `RTS.Game` assembly file in our project folder, which should be at `Assets/Scripts/Game/` and
 add `Unity.Addressables` and `Unity.ResourceManager` to our *Assembly Definition References*. Otherwise, our
  IDE won't be able to find the classes of this package. 

![RTS.Game assembly definition references]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_assemblyDefinition.png)

Nice! We are now good to go and can start coding. First we will create a very simple `AssetLoadingService`. It will
 handle finding and loading Assets via the Addressables package asynchronously. Create a `Assets/Game/AssetLoading` folder
 where we can put our two classes:
 - `AssetLoadService.cs`
 - `AssetType.cs`
 
Both classes will be very simple, to be precise, `AssetType` will just be an enum. Let's start with the
 `AssetLoadService` class.
 

{% gist d710ef843bc2829f406b15111578437c AssetLoadService.cs %}



That's already the whole class. I need to explain a few things here. First, I created an Interface so that we don't
 need to reference the implementation of the `AssetLoadService`. In this project we are using Addressables to load
  the assets. If we decide to load our assets differently in another project, we could still use the interface and
   just replace the implementation. That's always good.
   
Next, I decided to make the `LoadAsset<T>(..)` method generic. By doing so, we only need a single method to load all
 kinds of assets with it. We just need to pass the type of the asset, and we will get the asset with the expected
  type back.
  
  You might wonder why this method has a return type of `void` and returning the asset via a callback
   instead of returning it directly. That's because we are using Addressables and Addressables can only load assets
    *asynchronously*. The reason for that is, that it may take some time until the asset is loaded. Therefore, we
     cannot return it in the same stacktrace but use a callback which is invoked as soon as the job is done. If this
      is new to you, it might feel a little weird at the beginning, but you will get used to it. Asynchronous
       programming also requires doing things different than in regular synchronous programming (where you get the
        response right away), but you will see this later.

The Addressables system finds assets via keys (or addresses). These addresses are defined by us in the inspector. How
 exactly we will see later. We build our address from the `AssetType` and the `EntityType` which we didn't implement
  yet, but we will in a minute. Both are enum types, and we just separate them by a `/` character so that our address
   will look similar to a path e.g. `Buildings/BuildingA`. We also could have used the address directly to load our assets
   but then every script that wants to load an asset would need to know the correct address of the asset it wants to
     load. What if we decide to change the address or if we don't want to use Addressables anymore? In these cases we
      would need to change things in multiple classes which is a nightmare in bigger projects and a very bad practice
      . In general, if a scripts wants to load an asset it knows what it wants to load and which type it has
       (GameObject, Audio file, config file etc.).
      
Since we call the asynchronous `Addressables.LoadAssetAsync` method to load the asset, we need to subscribe to the
 `completed` callback, which is invoked when the asset has been loaded. Then we will just grab the result of the
  loading process, which will be the asset itself. 

#### The AssetType enum

The `AssetType` enum defines ass types of assets we would like to load in our game. This can be anything you like
. For now, we add just a couple. This might be extended later, we will need most of these types at a much later
 state of this project.

So let's create a new enum file called `AssetType.cs`, put it to `Assets/Scrips/Game/AssetLoading` and add some
 assetTypes to it.

{% gist 74938ee0d8515105588503638b7778e5 AssetType.cs %}

Since enums in C# are basically stored as integers we assign each assetType a value. Then we are able to add
 / remove assetType in between. If we wouldn't define values here, the first enum would have the value of 0 and then
  it would get incremented by 1 with each entry. If we then you add entries in between, the assigned integer values
   would change for all following entries and screw up the serialization in all places where we used this enum
   . Therefore, always pre-assign values when using enums is a good practice. I decided to let the `AssetType
   ` inherit from `byte` which is a not necessary optimization, but since I'm pretty sure we won't have more than 256
    different AssetTypes in the end, it would be overkill to use the default, which would be `integer`.

#### The EntityType enum

The `EntityType` enum is similar to the `AssetType` but instead of defining types of assets with it, we use the
 `EntityType` as a unique identifier for any asset we have in the game. So anything which we would like to *identify
 *, for whatever reason, we could give it an `EntityType`. It is worth noting that this unique identifier **does not**
  identify a specific instance of an entity. For example, we could have a tree in our game which could have the
   `EntityType` *Tree*. If we now instantiate this tree a 1000 times to create a forrest out of it. All trees would
    have the same `EntityType`. We could use this to get, for example, all trees in our game, but we cannot get the
     evil tree with number 666. For that we would need something like an `EntityId` to be able to identify
      specific instances, which we will create in a later tutorial. 

So let's create a new enum file called `EntityType.cs` and put it to `Assets/Scrips/Simulation/Data`. The whole
 folder structure does not exist yet. This is the first script which is part of our Simulation assembly. All script
  in this assembly will be used on the server / the other clients in the network or sent via the network. Therefore,
   we separate it from the scripts which are only needed or executed on the local client. 


{% gist 2702df03d9ddf0544b089549d7bf7773 EntityType.cs %}


As you can see I also already defined some arbitrary values to the enums. If you plan to have more than 500 unique
 Buildings, Units, or Resources in your game you should assign different values. The numbers for Buildings for
  example of course don't have to be consecutive and since we pre-assigned the values to the enums we can shuffle
   the order of them around, but personally I like to have everything nice and clean ^^'.

Okay, now let's leave the boring part behind and continue to implement some more game logic!

## Placing buildings

We can finally start with the topic of this tutorial. The building placement. This section will tackle the building
 placement and position validation by using colliders and ray-casting. The building construction will be
  finished instantly at first, but we will also add the possibility to define construction site, and a construction
   timers. To implement all of this, we will create four new classes and put them into the `Assets/GameBuildMode
   ` folder.
  
 - `BuildModeView.cs` 
 - `BuildModeService.cs` 
 - `ConstructionSiteView.cs`
 - `ConsturtionSiteViewData.cs`

### The BuildModeView class
 
Let's start with the `BuildModeView`. This class is a view component and inherits from `MonoBehaviour`. It will be
attached to a child GameObject of our buildable prefabs. There are as always multiple ways of achieving the desired
result, but I think this one is the most versatile one. For that, we need to set up the prefabs of our buildings. Let's
open the `BuildingA` prefab and add a new Quad 3D object to it called, `Footprint` or something similar. We also create
a new script called `BuildModeView.cs` and attach it to the `Foorptint` gameObject.
 
![Footprint child object setup]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_PrefabSetup_1.png)

As you can see in the screenshot above, the `BuildModeView.cs` has already some fields in the inspector. Let's add these
quickly as well as the public methods we will need.
 
 
{% gist b75ba09a423cb67e8807b20db1057341 BuildModeView.cs %}

`ShowPreview()` will be called when the BuildMode starts. In this method we enable our footprint quad to visualize how
much space our building requires. I decided to go with this approach instead of using the actual mesh collider of the
visible model for that because we have more options when doing so. We could set the footprint size to the exact size of
the mesh to be able to align our buildings without any gaps between them to build objects like walls etc. When we think
about factory buildings for example this might not be intended because when we build new units and the surrounding area
of the building is completely blocked by other buildings, what should we do then? We would need to cover this case. I
decided to go around that by increasing the footprint size for factories that it's guaranteed that Units always have
free space where they can be spawn. If you still want to be able to build factories directly next to each other, fine.
Set the footprint size to match the mesh size and implement logic the handle the case I described above.

To be able to enable the footprint mesh, we need a reference to the `MeshRenderer`. We already added that to the
 class above, now we need to assign it to the field. Afterwards we can enable the `MeshRenderer` when we start building.
Let's add that and also implement the remaining code of these public methods.

{% gist 2f527644a332a67fca1a4f9c18118668 BuildModeView.cs %}

We just added three new variables where we can store the data we need. In the `_collisionCounter` variable we will
keep track of all collisions that happened while we placed the building to find out if the placement is valid or not.
In the `IsPlacementValid()` we return `true` when the collision counter is exactly at 0. We don't count the collisions
currently, so this will always return `true` for now. The `SetMaterialTint()` method will handle the coloring of our
building while we didn't confirm the placement yet. To visualize whether the current position of our building is valid
we set the material color to either `white` or `red`. Let's assign a new Material to the footprint mesh in our
 inspector. I added a special shader to the project which you can use. This shader shows the outline of the footprint 
 mesh similar to the `CircularOverlap` shader we used in the previous tutorial. The shader I've created is very basic,
 so feel free to find or create a better one yourself. Create a new Material and assign the `SquareOutline` shader to
  it which you [can download here](https://gist.github.com/Cxyda/54accfe2d3b333852a028514ae5bb19d).

![Footprint child object setup]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_PrefabSetup_2.png)

The `BuildModeView` class controls the footprint. When we change the `_footprintSize` values in the inspector, the
footprint should update and adjust its size. To accomplish this we need to add some code which is executed in the
editor. Add the `[ExecuteInEditMode]` above the class and add two new methods, `Awake()` and OnValidate()`.

{% gist aeca5e3b053589326dcff5c843a13707 BuildModeView.cs %}

Both new methods are called in the Editor and on runtime. The code in the `Awake()` method should only be executed
 when we press play to make sure the MeshRenderer is being disabled in case we forgot to do so. The code in
 `OnValidate()` is executed everytime we change something in the inspector or when code compilation happens. Then we set
 the `localScale` of the footprint GameObject to the footprint size. We also go to the parent object and grab all
  `MeshRenderer` components in all children and store them. The reason for that is that most RTS games out there
   change the color of a building to red when the placement is invalid. Maybe your building model consists of multiple
   meshes and then we would need to change the color for all of them. This needs to be added to the `SetMaterialTint()`
   method.
   
{% gist 2e9f2ff2f9ab356163bffaedf90447c3 BuildModeView.cs %}

Nice. Unfortunately we need to add more code before we can actually test our new feature. Let's add a `BuildingView`
class which will be attached to all buildable objects. It is a general view class and serves as an interface for the
player and game services so that they can interact with the building.
 
{% gist c5561f4a26efe1ef5b5fb5d8321ffa3f BuildingView.cs %}

As you can see, this class has four public methods which contain only a few lines of code.

The `SetPosition(..)` is being called by the `BuildModeService` later. It sets the position of the transform and calls
the `CheckPlacement()` method. This will validate the position and tint the object red if the placement is invalid.

If the placement is valid, and the player confirms the position, the `ConfirmPlacement()` will be called. It will
 disable the model GameObject to hide the preview we saw in the build mode and call the `ConfirmPlacement()` method
 of the `BuildModeView`. At this point we will later spawn the construction site and wait until the construction has
 been finished. For now, we just call `ConstructionFinished()` so that we have instant building.
 
The `ConstructionFinished()` method enables the model again and will hide the construction site later. Currently this
doesn't make much sense, I know, but it will as soon as we implemented construction timers.

The `StartBuildMode()` method simply forwards the call to the `BuildModeView` to `ShowPreview()`

Add the `BuildingView` class to all of our buildable Prefabs and assign the model GameObject and a reference to the
`BuildModeView` component.

![Adding the VuildingView]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_PrefabSetup_3.png)

Since we are currently on it, also set up the Addressable addresses. To do so, select for example the `BuildingA` prefab
and tick the *Addressable* checkmark and enter `GameObject/BuildingA` for BuildingA, for BuildingB `GameObject
/BuildingB` and for BuildingC `GameObject/BuildingC`. Now our `AssetLoadService` is able to load these three
 buildings by their `EntityType`.

![Assigning Addresses]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_PrefabSetup_4.png)

Well done! We are getting closer. Now we can finally implement the service which handles our BuildMode.

 
### The BuildMode Service class
 
Next we implement the `BuildModeService` class which forms the core of this system. Let's start with the constructor
 and the dependencies we need for the service. As I already explained in the previous section we use *Zenject* for
  dependency injection. If you skipped the previous tutorial and you are unfamiliar with Zenject, I recommend reading
   the previous tutorial first.


{% gist 591f5cd62a19fc4bdf434868fcadc8b8 BuildModeService.cs %}


As you can see we need three classes which we already implemented the previous section and the `AssetLoadService` which
we created a minute ago minute. We add their interfaces as parameters to our constructor and then Zenject will handle
the reference injection for us. When the build mode is active, the player can confirm the building placement with the
 left mouse button and cancel it with the right mouse button. You can also bind the cancelation to the *ESC* key
  instead if you like. For the left and the right mouse button press we already have a callback in our
  `InputHandler` class, so let's subscribe to it and call `ConfirmPlacement` and `CancelBuildMode` methods when the
  events occur. Let's implement the logic form them and let's add the `BuildObjectOfType` method  as well which triggers
  the build mode when called.
  
{% gist cff24381d36eec3d8cbf683d5f645477 BuildModeService.cs %}


Let's quickly bind this class, as well as the `AssetLoadService` we created earlier, to Zenject, so we can test the
 state.

{% gist d403a1cb109a2d798eeb3a19a0079a43 GameInstaller.cs %}


Before we can test our progress we need to update the building position when the build mode is active according to
the mouse cursor position so that the player can control it's the placement of the building. We also need to a way to
actually start the build mode. Later, this will happen when the player clicks in the BuildMenu UI on a certain
buildingType, but for now we simply fake this and bind the "B" key to trigger the BuildMode. The position update of
 the building will happen in the `LateTick` method. You may remember that method. It comes with Zenject and is called
  when Unity calls `LateUpdate`. To be able to use it our `BuildModeService` needs to implement the `ILateTickable`
  interface.

{% gist c38c1971c2ea9927569865cdc4e692fb BuildModeService.cs %}


The check for the "B" button press can be removed after the next tutorial where we implement a UI for our game.

The mouse cursor position is in Screen Space, to get the actual World Space position we need to do a ray-cast from the
camera to the terrain. The position where the ray hits the terrain is the position where we want to place our
 building. At the top of our `BuildModeService` I also added a `TerrainLayerId = 6` constant. This could of course also
 be read from some game config file. For now, it will stay within this class.

Okay, we are finally ready to test what we implemented so far. Fingers crossed that it's working.

![Building Placement WIP]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_BuildingPlacement_1.gif)


Great! It is indeed working. The building follows the mouse cursor and if we use the left / right mouse buttons we
confirm / cancel the placement. You may notice two things. The placement is jumping a lot and we have a
**NullReferenceException**. We will fix both now.

First, the building placement is not smooth and is jumping around, that's because the rays we cast from the camera
through our mouse position now hit the colliders of our attached building. We need to fix this, one thing how we can
fix it is to move our instantiated building and all of its children to the *Ignore Raycast* layer. Then no ray-cast
will hit any of the colliders. The downside is that we would need to store the layer the building, move all
gameObjects in the hierarchy to the new layer when instantiating the building and move all of them back when the
placement has been confirmed. This can be costly, especially when the building hierarchy is big, but since that won't
be the case and it will only happen once in a while we will choose this approach. If your project has different needs,
you may consider other approaches. We already store the `_defaultLayer` in our local `OnLoaded(..)` method of the
`BuildObjectOfType(..)` method. Right below it we call `SetLayerRecursively(..)`. We also need to move the objects
back to the original layer when the player placed the building. Let's add that to the `ConfirmPlacement()` method as
well.

{% gist 9d400633b4f7c08c067a1e7c10e9dbfb BuildModeService.cs %}

![Building Placement WIP]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_BuildingPlacement_2.gif)


This already looks much smoother. Nice!

We only store the layer of the building prefab itself and move all objects in the hierarchy back to this layer when we
are done. This will lead to issues when your prefabs have objects in the hierarchy that are placed on different layers.
Then you would need to store the layer of each object.

Next, if you have looked at your console output you will see at least one **NullReferenceException**. Why is that?
The reason for that is, because we are using Zenject. Some components on our  new prefabs are using Zenjects `[Inject]`
attribute. Since we are instantiating our new Prefab by using Unity's standard `Object.Instantiate(..)` method,
Zenject has no chance of injecting the required dependencies before the object is created and therefore the reference
to the `SelectionService` for example is null. We can fix that by creating a factory method which handles the
instantiation of our new prefab and which injects the dependencies. To use a factory method to create new objects has
another advantage. When we do so, it's much easier for us later on to implement object pooling. Imagine we have
hundreds of units fighting against each other and everytime a unit gets  killed or created we destroy or instantiate
a new object. This is not ideal. It would be better to use an object pool  from where we can get a new object if we
need one and if a unit gets killed in the game, we simple move it back to  this pool and hide it in the game. This
approach takes far less system resources. We won't add this now. For now, we only implement a simple Factory class.

#### Adding a Prefab Factory

Create a new class called `PrefabFactory` and put it into the `Assets/Scripts/Game/Utility` folder.

{% gist 491287395c1f7b4ae53f1c4b9070852d PrefabFactory.cs %}


In the constructor, Zenject is injecting the `DiContainer` class which is the dependency injection container. This class
contains several methods to instantiate various objects. For now, we only need the `InstantiatePrefab(..)` method. It
accepts the same parameters as the `Object.Instantiate(..)` method and returns a gameObject as expected.

We also need to bind this method in our `GameInstaller` class.

{% gist fb4fc5f3631029752575f371aed572c8 GameInstaller.cs %}


Nice. Now we need to go back to our `BuildModeService` class and change a couple of things.

1) We need to add the `IPrefabFactory` to our constructor and add a field called `_prefabFactory` to store the
reference.

2) we need to replace the `Object.Instantiate(gameObject)` call in our `BuildObjectOfType(..)` method to use our new
prefab factory. Use `_prefabFactory.CreateGameObject(gameObject)`
instead.

3) We call `Object.Destroy(_buildablePreview.gameObject)` in the `CancelBuildMode()` method. Replace this with
`_prefabFactory.ReleaseGameObject(_buildablePreview.gameObject)`.

Done! The full class until now looks like this:

{% gist 408ff4863c3bef7fa00714342041711e BuildModeService.cs %}

Awesome! We are now able to instantly build new buildings by pressing the "B" button, on **any** location. We need to
 handle collision with other buildings and uneven terrain so let's do that now. 

### Handling collision

For collision handling we need two things. *Colliders* and *RigidBodies*. Without a `RigidBody` Component, Unity's
`OnCollision` and `OnTrigger` methods won't be called when colliders intersect. Since our script is not working when
somebody forgets to add these components, let's enforce it. We can simple add the `[RequiredComponent]` attribute above
of our `BuildModeView` class.

{% gist 408ff4863c3bef7fa00714342041711e BuildModeView.cs %}

This will create a `BoxCollider` component and a `RigidBody` component the next time you give the Unity Window focus.
Great! Now we need to get our collider and set it up. I don't want to do the work to assign the collider manually
every time so we will let our script handle that. Since our script is running in the Edit mode as well, we can get it
 there and there is no need to get it on runtime of the game. Create a `_private BoxCollider _footprintCollider`
 variable at the top of our class and add the `[SerializeField]` attribute to it. Otherwise, it won't be serialized and
  will be null when we build our game to ship it to our customers. Since we get the component automatically let's hide
  the field in the inspector by also adding the `[HideInInspector]` attribute. Now all we need to do is to call
  `_footprintCollider = GetComponent<BoxCollider>();` to our `OnValidate()` method to get the component.

{% gist 0f7270c8d8086ee842f0fb746c7df3dd BuildModeView.cs %}

Now we need to implement `OnTriggerEnter` and `OnTriggerExit` which will be called by Unity as soon as a collision
with another Trigger Collider happens. At least one of these components needs to have a `RigidBody` component, but we
covered that with our `RequireComponent` attribute above. 

{% gist 2a3c5c93cf6d0ea725eb7ffa90e74b6e BuildModeView.cs %}

We increase the collision counter when a collision happens with an object that is not on the Terrain layer and we
decrease it when the Trigger leaves our own collider. If you now test our progress you will see that our placement
is constantly invalid. The reason for that is, that our model has a collider as well. When we instantiate the prefab,
the `OnTriggerEnter` method is called on both gameObjects if at least one Trigger Collider is involved. The solution for
this would be to deactivating all colliders while we are previewing the new building. To do so, we need to get all
colliders in the hierarchy.

{% gist 3b28241302c403391a878dedb97a45f3 BuildModeView.cs %}

Add a `ActivateOtherCollidersThanSelf(..)` call to `ShowPreview()` and `ConfirmPlacement()` and we are finally done.

![Building Placement WIP]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_BuildingPlacement_3.gif)


#### Handling uneven Terrain

To handle uneven terrain, we will do ray-casts from the footprint downwards. If we hit the terrain within a certain
range, we consider the placement as valid. To get a good and reliable result, we need to do multiple ray-casts. We could
use all four corner points but for very large buildings, we could miss a mountain or canyon right in the center of the
building. Therefore, we will do a ray-cast every unit instead. We are going to make this customizable, so if your world
uses a different scale, you could change that. We will add all required code to the `BuildModeView` class. So let's
open it up.

We begin at the `IsPlacementValid()` method. The first thing we need to do is to get the corner points of our footprint
object. Create a `GetBaseBoundPoints(..)` method and change the existing code a little, so that we don't just return
 `_collisionCounter == 0`.
 
{% gist 9eab6dcdec1337133e9940a2d3681188 BuildModeView.cs %}

Okay, that was maybe a bit too fast, but I added some comments so that you should have understood what we are
doing there. I also added a couple of new variables and I quickly want to mention `_tempPointsList`. This is a temporary
list which holds the calculated points. Since this code is executed every frame when we want to build a new building.
We would create every frame a new list and when we are done with the list at the end of the frame the C#
garbage collector would kick and remove the list from the memory. That's not very efficient, so why not create this
list at the beginning and keep it? That sounds like a good plan. We could (and should) at some point even consider an
Object Pool for lists to be able to recycle our lists globally in our game. For now, we just go with a single, temporary
list which we will re-use. If you do that. Don't forget to clear the list every time before using it. Otherwise the old
data will still be present. Let's add all new variables at the top of our class. This is how it should look now for you.

{% gist 2bcd7da4777ec3256b268c30d6b9a60b BuildModeView.cs %}

Now, let's start casting rays from our calculated points to check whether our building is above the Terrain. To do so,
we create a `TryGetHit(..)` method and call it in our `foreach` loop. We cannot use our existing `CameraRaycastHandler`
since this is using the camera as origin to cast rays from. We also need to define a `RayLength` at the top of the
class.

{% gist 8558f2a0787cc59d164325e670d3ce04 BuildModeView.cs %}

If you look closely at line 31 where we spawn create the ray, you recognize that we move the ray half the distance up
first, before we cast it the downwards at the full length. The reason for this is that our building center is placed
exactly on the terrain, but the bounds could be above or below it. When we cast a ray from below the terrain downwards,
we will of course never hit it. Even if the terrain would be in an acceptable distance. Therefore, we first move it up
a bit and then cast downwards.

This is already working, but we cannot what it is actually doing and therefore it's hard to understand. Let's draw some
Gizmos in the Editor to understand what's going on. Add a `OnDrawGizmos()` method somewhere in the class.

{% gist 423b95d665546b9bb37c3e9604a962d4 BuildModeView.cs %}

![Building Placement WIP]({{site.baseurl}}/images/resources/MiniRTS_series/BuildingPlacement_BuildingPlacement_4.gif)

Awesome! Now our building placing is respecting collisions as well as Terrain elevation, and we can see the rays in
 the scene view. We are basically done now. The `BuildModeService` is able to start and cancel the placement of a new
 building as well as finish the placement on valid positions. But there are two small issues with it. The service does
 not ask other systems if the player for example has enough money to place down the building. To do so, we will add a
 callback where every other system can subscribe to, to do some checks and validate the placement on their side when
 the player confirms the placement. Only if all subscribers return `True`, the `BuildModeService` will finally accept
 the placement. Let's open the `BuildModeSerive` and add a `Func<EntityType, bool>` delegate and a new method called
 `DoAllSubscribersConfirm()`. We call this new method within `ConfirmPlacement()`.
 
 {% gist 86fee12e0f59edfc98dfe18a0f6853ac BuildModeView.cs %}

If you are unfamiliar with C#'s `Func` delegates, it is basically an `Action` which has a return value. Every method
that subscribes to that event needs to return a bool value. Unfortunately, by default only the last return value is
considered and all others are ignored. That would not work for our use case so we need to call `GetInvocationList()` on
our delegate and get all subscribers from it. Then we iterate over all subscribers and invoke the event to get the
return values one by one. If any subscriber returns false, we stop checking and return false. Since
`GetInvocationList()` return a `Delegate[]`, we need to cast the `Delegate` in our `foreach` loop to the correct type,
which is `Func<EntityType, bool>`.

The last very tiny thing is that we should not allow to start the build mode when it is already active. You can
currently do that by pressing the "B" key multiple times without confirming the placement. That won't happen in our
game later if we implement our systems right but it's easy to check that. Just add `if(_isBuildModeActive) return;` at
the very top of our `BuildObjectOfType(..)` method and we are good.

Very nice! Phew that was a ride! You've done it! You can be proud of yourself. That was a lot of work to implement
such a simple sounding feature, but we did it the right way and now we can add this system to a lot of different games
if we like.

[The full code of all classes can be found in my GitHub Repository](https://github.com/Cxyda/MiniRTS-Tutorial/tree/0.3)

Next we will look into Construction sites and unit production!

##### [< Input and Selection Handling]({% post_url 2021-10-28-MiniRTS-SelectionAndInputHandling %}) | Construction sites and Factories >