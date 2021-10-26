---
layout: post
title:  MiniRTS - 02 Project Setup
categories: [C#,Unity3D,MiniRTS]
---

In this short section we will just setup the basic project structure. As mentioned before, I will use the Zenject (Extenject) framework for [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection). If you never heard of Zenject or even Dependency Injection I advise you to get familiar with this concept. It is super helpful and makes your life much easier when working on bigger projects or with multiple people on a single codebase.
Zenject is the original name of the Dependency Injection framework of Unity. It got abandoned at some point and development got continued in *Extenject* so they are basically the same.

[You can download the project files from my GitHub repository](https://github.com/Cxyda/MiniRTS-Tutorial/releases/tag/0.1) where Extenject is already added. In that project you also find Prefabs, materials, shaders and textures for you ready to use. You can of course start from scratch and do everything on your own. But, I won't explain every step in detail so more knowledge about Unity and other tools like Photoshop may be required to follow along. So if you did download the project I've provided you you can basically skip the next sections and proceed with m,y next blog post about Selection and Input Handling.

If you didn't already, start by creating a standard Unity3D project. When Unity is ready go to *Window -> Package Manager* and search for 'Extenject' in the Unity Registry. Install that package and add it to your project.
In your Assets folder in Unity create a couple more folders like so:

![Project folder structore]({{site.baseurl}}/images/resources/MiniRTS_series/ProjectSetup_FolderStructure.png)

In `Content` we will put all Meshes, Prefabs, Textures, Materials etc. In `Scripts` we will put the code we write in this series. `Scripts` will contain a `Game` and a `Simulation` folder. For now, we only will add Game code and later handle the Simulation related code. Please also create an [assembly definition file](https://docs.unity3d.com/Manual/ScriptCompilationAssemblyDefinitionFiles.html) in the `Game` folder called `RTS.Game`. Assembly definition files are handy and force you, if used properly, to think more about dependencies and help you to maintain a cleaner project. They can also speed up compilation times in bigger projects a lot when used wisely. If you never heard about assembly definition files I advise you to read the link above but in short, they separate your code so that you cannot access the code of other assembly definitions easily. If you want to do so, you have to add the other assembly definitions as a reference. Which we will do now.

First create an assembly definition file in `Assets/Scripts/Game/` by right clicking in the project folder `Create -> Assembly Definition` and call it `RTS.Game`. 
To be able to access the `Zenject` classes from our classes in our `RTS.Game` assembly, we need to select the `RTS.Game` assembly definition file and configure it like below.
   
![RTS.Game assembly definition setup]({{site.baseurl}}/images/resources/MiniRTS_series/ProjectSetup_GameAssemblyDefinition.png)

We need to do one more thing. Setup a *Scene Context* for [Zenject(https://github.com/modesttree/Zenject)] which handles our Bindings. To do so, create a new Scene and name it whatever you like. In the *Hierarchy* window, right-click any empty space and select `Zenject -> Scene Context`. This will create a GameObject called `SceneContext` with a `Scene Context` component attached. This component has basically three different lists of installers which are all empty for now. There are
- Scriptable Object Installers (classes that inherit from `ScriptableObjectInstaller`)
- Mono Installers (classes that inherit from `MonoInstaller<T>`)
- Prefab Installers

Installers in Zenject are classes that are responsible for Binding classes and / or interface so that they can be injected into (referenced by) other classes. If you are unfamiliar with this concept I advise you to read at least the first sections in the [Zenject documentation](https://github.com/modesttree/Zenject).

Create a new component class called `GameInstaller`, attach it to the `SceneContext` gameObject and assign it to the `Mono Installers` list. 

![RTS.Game assembly definition setup]({{site.baseurl}}/images/resources/MiniRTS_series/ProjectSetup_SceneContextGameInstaller.png)

Open the `GameInstaller.cs` file in an IDE of your choice. I'm using [JetBrain's Rider](https://www.jetbrains.com/de-de/rider/). There is not much to do here so just type the following:
```csharp
using Game.InputHandling;
using Game.Selection;
using Zenject;

namespace Game.Installers
{
	/// <summary>
	/// This class installs the core game systems
	/// </summary>
	public class GameInstaller : MonoInstaller<GameInstaller>
	{
		public override void InstallBindings()
		{
            // our bindings will go here
		}
	}
}
```

Nice. That's it already. In the next section we will extend this class and add our bindings there. 

If you had issues to follow remember that you always can check out my GitHub repository. You should definitely [check out / download the files](https://github.com/Cxyda/MiniRTS-Tutorial/releases/tag/0.1) in the `Content` folder. This series expects you to have certain assets like Prefabs and Shaders etc.

In the next blogpost we will finally start with our first game systems which are crucial for any RTS game: Object Selection and Input Handling.

##### [< Introduction]({% post_url 2021-10-22-MiniRTS-introduction %}) | [Selection and input handling >]({% post_url 2021-10-23-MiniRTS-SelectionAndInputHandling %})
