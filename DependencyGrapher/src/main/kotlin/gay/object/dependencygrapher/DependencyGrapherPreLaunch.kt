package gay.`object`.dependencygrapher

import gay.`object`.dependencygrapher.api.DependencyGraph
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.encodeToStream
import net.fabricmc.loader.api.FabricLoader
import net.fabricmc.loader.api.ModContainer
import net.fabricmc.loader.api.entrypoint.PreLaunchEntrypoint
import net.fabricmc.loader.api.metadata.ModDependency
import net.fabricmc.loader.api.metadata.ModOrigin
import org.slf4j.LoggerFactory
import kotlin.io.path.div
import kotlin.io.path.outputStream

object DependencyGrapherPreLaunch : PreLaunchEntrypoint {
    private val logger = LoggerFactory.getLogger("dependencygrapher")
	private val jsonSerializer = Json {
		prettyPrint = true
	}

	@OptIn(ExperimentalSerializationApi::class)
	override fun onPreLaunch() {
		val graph = DependencyGraph.empty()

		logInfo("Finding canonical mods.")

		val canonicalMods = mutableMapOf<String, ModContainer>()
		for (mod in FabricLoader.getInstance().allMods) {
			if (mod.metadata.type == "builtin" || mod.metadata.id == "dependencygrapher") {
				logInfo("Skipping mod: ${mod.metadata.id}")
				continue
			}
			logInfo("Discovering mod: ${mod.metadata.id}")

			var canonicalMod = mod
			while (canonicalMod.containingMod.isPresent && canonicalMod.origin.kind != ModOrigin.Kind.PATH) {
				val parent = canonicalMod.containingMod.get()
				if (canonicalMod.metadata.id == parent.metadata.id) {
					throw RuntimeException("Infinite loop detected, please update Quilt Loader to >=0.28.1 (see https://github.com/QuiltMC/quilt-loader/issues/470)")
				}
				canonicalMod = parent
				logInfo("  Parent: ${canonicalMod.metadata.id}")
			}

			if (canonicalMod.origin.kind == ModOrigin.Kind.PATH) {
				canonicalMods[mod.metadata.id] = canonicalMod

				if (canonicalMod.metadata.id !in graph.jars) {
					graph.jars[canonicalMod.metadata.id] = canonicalMod.origin.paths
						.map { it.toString() }
						.toMutableSet()
				}
			} else {
				logInfo("  Skipping mod: ${mod.metadata.id} (non-path parent: ${canonicalMod.metadata.id})")
			}
		}

		logInfo("Adding dependencies.")

		for (mod in FabricLoader.getInstance().allMods) {
			val canonicalMod = canonicalMods[mod.metadata.id] ?: continue

			graph.addDependencies(
				canonicalMod.metadata.id,
				mod.metadata.dependencies
					.filter { it.kind == ModDependency.Kind.DEPENDS }
					.mapNotNull { canonicalMods[it.modId]?.metadata?.id }
					.filter { it != mod.metadata.id }
			)
		}

		val outputPath = FabricLoader.getInstance().gameDir / "dependencygrapher.json"
		logInfo("Writing dependency graph to file: $outputPath")
		jsonSerializer.encodeToStream(graph, outputPath.outputStream())
	}

	private fun logInfo(message: String) {
		logger.info("[DependencyGrapher] $message")
	}
}
