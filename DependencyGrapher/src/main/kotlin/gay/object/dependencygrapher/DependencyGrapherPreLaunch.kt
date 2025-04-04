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
		logger.info("Building dependency graph")

		val graph = DependencyGraph.empty()

		val canonicalMods = mutableMapOf<String, ModContainer>()
		for (mod in FabricLoader.getInstance().allMods) {
			if (mod.metadata.type == "builtin" || mod.metadata.id == "dependencygrapher") continue

			var canonicalMod = mod
			while (canonicalMod.containingMod.isPresent) {
				canonicalMod = canonicalMod.containingMod.get()
			}

			if (canonicalMod.origin.kind == ModOrigin.Kind.PATH) {
				canonicalMods[mod.metadata.id] = canonicalMod

				if (canonicalMod.metadata.id !in graph.jars) {
					graph.jars[canonicalMod.metadata.id] = canonicalMod.origin.paths
						.map { it.toString() }
						.toMutableSet()
				}
			}
		}

		for (mod in FabricLoader.getInstance().allMods) {
			val canonicalMod = canonicalMods[mod.metadata.id] ?: continue

			graph.addDependencies(
				canonicalMod.metadata.id,
				mod.metadata.dependencies
					.filter { it.kind == ModDependency.Kind.DEPENDS }
					.mapNotNull { canonicalMods[it.modId]?.metadata?.id }
			)
		}

		val outputPath = FabricLoader.getInstance().gameDir / "dependencygrapher.json"
		logger.info("Writing dependency graph to $outputPath")
		jsonSerializer.encodeToStream(graph, outputPath.outputStream())
	}
}
